# DESCRIPTION:
# pipeline.r is the main wrapper of all the scripts for papr. Additionally, it 
# provides the methods to parse the command line arguments.
print("Setting pipeline")
library(rjson)
library(tidyverse)
# library(dplyr)
library(magrittr)
library(data.table)
library(ggpubr)
# library(gridExtra)
library(kableExtra)
# library(stargazer)
# library(argparse)
# library(papeR)
# library(foreach)
library(rmarkdown)
library(argparser)
library(lme4)
library(lmerTest)
# library(afex)
# library(tidyverse)
library(multcomp)
# library(emmeans)
library(xtable)
library(tidyselect)
library(ggthemes)
library(RColorBrewer)
library(openxlsx)

# This script combines pipeline definition + data importing when running new models on data saved in an R environment.
# This is used when running new models on data that has already been passed through and saved by BASSPRO-StAGG in a previous run.

################### Adds arguments that are inserted to the terminal for file locations ####################
# Arguments to be defined in the command line call; these are read via the add_argument function.

p <- arg_parser("Run STAGR")

p <- add_argument (p, "--dir", help="Set the working directory for R, should be Mothership")

p <- add_argument (p, "--JSON", help="Filepath to location of folder with all JSON files from Breathcaller")

p <- add_argument (p, "--R_config", help="Filepath to properly formatted R Configuration sheet")

p <- add_argument (p, "--Graph", help="Filepath to properly formatted Graph Configuration sheet")

p <- add_argument (p, "--Foxtrot", help="Filepath to properly formatted Optional Graph configuration sheet")

p <- add_argument (p, "--Output", help="Filepath to folder that the graphs will be saved in")

p <- add_argument (p, "--Tibblemaker", help="Filepath to tibblemaker R code to read in all files")

p <- add_argument (p, "--Stat", help="Filepath to statistics code in R")

p <- add_argument (p, "--Makegraph", help="Filepath to base graph making R code")

p <- add_argument (p, "--Bodytemp", help="Filepath to R code for other graphs")

p <- add_argument (p, "--I", help="Type of image to output")

# Arguments are imported + stored as a list with the names defined as above.
args2 <- parse_args(p)


print("Loading data")

#########################
#####JSON LOCATION#######
#########################

# Sets working directory to the Mothership so arguments in command line that indicate file locations are 
# understood and found by R.
setwd(args2$dir)

# Load data from R environment.
load_env <- grep("\\.RData", args2$JSON, value = TRUE)
if(length(load_env) == 0) {
  print("No R environment selected.")
} else if (length(load_env) > 1) {
  print("Multiple R environments selected; only the first will be used.")
}
load(load_env[1])

# Remove conflicting arguments.
args <- args2
rm(load_ev, args2)

#########################
#####APPEND JSONS########
#########################

# Function to append new JSONs to the tibble loaded from the R environment.
## Inputs:
### fp: character vector, Filepaths of desired files
### breath_df: data frame/tibble, old currently existing data frame
## Outputs:
### breath_df: data frame/tibble, new data for analysis.
simple_appender <- import_data <- function(fp, breath_df = NULL){
  #Function to convert NULL and "" values in the raw json to NA (necessitated by R handling of NULL values)
  blank_to_na <- function(xx){
    new_xx <- unlist(lapply(xx, function(x) ifelse(((x == "")|(is.na(x))|(x == "NA")), NA, x)))
    return(new_xx)
  }
  
  null_to_na <- function(xx){
    new_xx <- unlist(lapply(xx, function(x) ifelse(is.null(x), NA, x)))
    return(new_xx)
  }
  
  #For each mouse, import and attach to overall tbl.
  for(ii in fp){
    if(grepl("config", ii)) {next}
    print(paste0("Adding file:", ii))
    
    #Raw import
    temp_json <- rjson::fromJSON(file = ii, simplify = FALSE)
    
    #Convert NULL to NA
    temp_list <- lapply(temp_json, null_to_na)
    temp_list <- lapply(temp_list, blank_to_na)
    
    # Turn json to tbl
    temp_df <- as_tibble(temp_list)
    
    if(is.null("breath_df")){
      # Create breath_df
      breath_df <- temp_df 
    } else {
      # Check if types match
      for(col_num in 1:ncol(breath_df)){
        col_name <- colnames(breath_df)[col_num]
        if((!is.null(temp_df[[col_name]])) & (class(breath_df[[col_name]]) != class(temp_df[[col_name]]))) {
          breath_df[[col_name]] <- as.character(breath_df[[col_name]])
          temp_df[[col_name]] <- as.character(temp_df[[col_name]])
        }
      }
      # Attach to overall tbl.
      breath_df <- bind_rows(breath_df, temp_df)
    }
    
  }
  
  # Check if character column should be numeric
  for(col_num in 1:ncol(breath_df)){
    suppressWarnings(temp_comp <- as.numeric(breath_df[[col_num]]))
    if(sum(is.na(breath_df[[col_num]])) == sum(is.na(temp_comp))) {
      breath_df[[col_num]] <- temp_comp
    }
  }
  
  return(breath_df)
} 

# Find JSONs in filepaths from command line arguments.
full_dirs <- unlist(strsplit(args$JSON, ","))
filepaths <- c(list.files(full_dirs, pattern = "\\.json", full.names = TRUE, recursive = TRUE),
               grep("\\.json", full_dirs, value = TRUE))

# 
if(length(filepaths) > 0) {
  tbl0 <- simple_appender(filepaths, tbl0)
}


#########################
#### R CONFIGURATION ####
#########################
#Loads R configuration file. This file has settings for independent, dependent, and covariate variables;
#body weight and temperature; and alias assignment if a variable name change is desired by the user.


if((!is.null(args$R_config)) && (!is.na(args$R_config)) && (args$R_config != "None")) {
  print("Loading new variable configuration")
  var_names <- read.csv(args$R_config, stringsAsFactors=FALSE, na.strings = c("NA", "", " "))
  #Convert to names without units.
  var_names$With_units <- var_names$Alias
  var_names$Alias <- sapply(var_names$With_units, wu_convert)
  
  #Sets columns names to designated alias names. These aliases are set by the user in the GUI. 
  setnames(tbl0, old = c(var_names$Column), new = c(var_names$Alias), skip_absent = TRUE)
  
  #Sets statistical values for dependent, independent, and covariate varibales based on R_config file.
  response_vars <- var_names$Alias[which(var_names$Dependent != 0)]
  covariates <- var_names$Alias[which(var_names$Covariate != 0)]
  interaction_vars <- var_names$Alias[which(var_names$Independent != 0)]
  
  #Custom graph ranges
  ymins <- as.numeric(var_names$ymin[which(var_names$Dependent != 0)])
  ymaxes <- as.numeric(var_names$ymax[which(var_names$Dependent != 0)])
  
  
  # Correct for user settings
  for(jj in interaction_vars){
    if(typeof(tbl0[[jj]]) == "numeric"){
      tbl0[[jj]] <- as.character(tbl0[[jj]])
    }
    if(length(unique(tbl0[[jj]])) == 1){
      warning(paste0("Independent variable ", jj, " has only one unique value. Results may be unreliable."))
    }
    if(length(unique(tbl0[[jj]])) > 20){
      warning(paste0("Independent variable ", jj, " has many unique values; this may cause memory issues. Should this be a covariate?"))
    }
  }
  
  for(jj in covariates){
    if(length(unique(tbl0[[jj]])) == 1){
      warning(paste0("Covariate ", jj, " has only one unique value. Results may be unreliable."))
    }
  }
  
  #Determines if extra graphs are plotted per user choices.
  spec_vars <- var_names$Alias[which(var_names$Spectral != 0)]
  poincare_vars <- var_names$Alias[which(var_names$Poincare != 0)]
  transform_set <- var_names$Transformation[which(var_names$Dependent != 0)]
  
} else {
  print("Keeping old variable configuration")
}


#########################
##### GRAPH CONFIG ######
#########################

if((!is.null(args$Graph)) && (!is.na(args$Graph)) && (args$Graph != "None")) {
  
  #Load Graph configuration file.
  print("Loading new graph settings")
  graph_vars <- read.csv(args$Graph, stringsAsFactors = FALSE)
  graph_vars$Alias <- as.character(graph_vars$Alias)
  graph_vars$Role <- as.numeric(graph_vars$Role)
  
  #Convert to names without units.
  graph_vars$With_units <- as.character(graph_vars$Alias)
  graph_vars$Alias <- sapply(graph_vars$With_units, wu_convert)
  
  #Sets statistical values for dependent, independent, and covariate variables based on R_config file.
  xvar_wu <- graph_vars$With_units[which(graph_vars$Role == 1)]
  pointdodge_wu <- graph_vars$With_units[which(graph_vars$Role == 2)]
  facet1_wu <- graph_vars$With_units[which(graph_vars$Role == 3)]
  facet2_wu <- graph_vars$With_units[which(graph_vars$Role == 4)]
  
  xvar <- graph_vars$Alias[which(graph_vars$Role == 1)]
  pointdodge <- graph_vars$Alias[which(graph_vars$Role == 2)]
  facet1 <- graph_vars$Alias[which(graph_vars$Role == 3)]
  facet2 <- graph_vars$Alias[which(graph_vars$Role == 4)]
} else {
  print("Keeping old graph configuration")
}



# Checks that graphing variables are categorical
for(gg in c(xvar, pointdodge, facet1, facet2)){
  if(length(unique(tbl0[[gg]])) > 8) {
    warning(paste0("Graphing variable ", gg, " has more than 8 categories; your graphs may become illegible. Is this a numeric variable?"))}
}

#########################
### USER GRAPH CONFIG ###
#########################

if((!is.null(args$Foxtrot)) && (!is.na(args$Foxtrot)) && (args$Foxtrot != "None")) {
  print("Loading new optional graph settings")
  other_config <- read.csv(args$Foxtrot, stringsAsFactors = FALSE, na.strings = c("", " ", "NA"))
} else {
  print("Keeping old optional graph configuration")
}


##########################
## Character Conversion ##
##########################

for(ii in 1:ncol(tbl0)){
  if(typeof(tbl0[[ii]]) == "character"){
    tbl0[[ii]] <- str_trunc(tbl0[[ii]], 25, side = "center", ellipsis = "___")
  }
}

rm(mod_res)
rm(mod_res_list)
rm(tukey_res_list)
rm(graph_df)

# print("Saving environment")
# save.image(file="./myEnv.RData")
save_atp <- try(save.image(file=paste0(args$Output, "/myEnv_",format(Sys.time(),'%Y%m%d_%H%M%S'),".RData")))
if(class(save_atp) == "try-error") {save.image(file=paste0("./myEnv_", format(Sys.time(),'%Y%m%d_%H%M%S'),".RData"))}

################### Designates location and names of the following R source codes to run ####################

#source(args$Tibblemaker)
source(args$Stat)
source(args$Makegraph)
source(args$Bodytemp)
