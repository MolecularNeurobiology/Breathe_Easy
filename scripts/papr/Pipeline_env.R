#########################
########Licensing########
#########################
# Breathe Easy - an automated waveform analysis pipeline
# Copyright (C) 2022  
# Savannah Lusk, Andersen Chang, 
# Avery Twitchell-Heyne, Shaun Fattig, 
# Christopher Scott Ward, Russell Ray.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.


#########################
#######DESCRIPTION#######
#########################
# pipeline.r is the main wrapper of all the scripts for papr. 
# Additionally, it provides the methods to parse the command line arguments and loads necessary libraries.
# This script combines pipeline definition + data importing when running new models on data saved in an R environment.
## This is used when running new models on data that has already been passed through and saved by BASSPRO-STAGG in a previous run.

#########################
####### LIBRARIES #######
#########################
#Loads required libraries for all following R scripts into the R environment. 
print("Setting pipeline")
print("current directory")
print(getwd())

required_libs <- c("rjson", "tidyverse", "magrittr", "data.table",
                   "ggpubr", "kableExtra", "rmarkdown", "argparser",
                   "lme4", "lmerTest", "multcomp", "xtable", 
                   "tidyselect", "ggthemes", "RColorBrewer", "openxlsx",
                   "reshape2", "svglite")

for(libb in required_libs){
  lib_test <- eval(parse(text = paste0("require(", libb, ")")))
  if(!lib_test){
    install.packages(libb, repos = "http://cran.r-project.org/", dependencies = TRUE)
    lib_test_install <- eval(parse(text = paste0("require(", libb, ")")))
    if(!lib_test_install & libb == "rjson"){
      install.packages("http://cran.r-project.org/src/contrib/Archive/rjson/rjson_0.2.20.tar.gz",
                       repos = NULL, type = "source")
    }
  }
}

pandoc_info = find_pandoc(dir="../pandoc-2.18/")
pandoc_absolute = normalizePath(pandoc_info$dir)
find_pandoc(cache = FALSE, dir=pandoc_absolute)

#########################
#####ADD ARGUMENTS#######
#########################
# Adds arguments that are inserted to the terminal for file locations.
# Arguments to be defined in the command line call; these are read via the add_argument function.

p <- arg_parser("Run STAGR")

p <- add_argument (p, "--dir", help="Set the working directory for R")

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

p <- add_argument (p, "--Sum", help="Filepath to directory with R markdown code for summary html", short = "-u")

# Arguments are imported + stored as a list with the names defined as above.
args2 <- parse_args(p)

# Save list of arguments
sink(paste0(args2$Output, "/CommandLineArgs.txt"))
print(args2)
sink()

print("Loading data")

#########################
#####JSON LOCATION#######
#########################
# Sets working directory to the chosen working directory so arguments in command line that indicate file locations are 
# understood and found by R.
starting_wd_new = getwd()
setwd(args2$dir)

# Find RData file.
## Assume that all files are listed in a text file pointed at by args2$JSON. 
## Newline separated text file.
full_dirs <- unlist(read.delim(args2$JSON, sep = "\n", header = FALSE))
renv_dir <-  grep("\\.RData", full_dirs, value = TRUE)

# Should only be one Rdata file selected.
if(length(renv_dir) > 1){
  stop("More than one Rdata file selected.")
}

# Load environment.
load(renv_dir)

# Remove conflicting arguments.
args <- args2
starting_wd <- starting_wd_new
rm(starting_wd_new)
rm(args2)

#########################
#####APPEND JSONS########
#########################
# Function to append new JSONs to the tibble loaded from an existing R environment.
## Inputs:
### fp: character vector, Filepaths of desired files
### breath_df: data frame/tibble, old currently existing data frame
## Outputs:
### breath_df: data frame/tibble, new data for analysis.
simple_appender <- function(fp, breath_df = NULL){
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

# Find + load JSON files.
## Assume that all json files are listed in a text file pointed at by args$JSON. 
## Newline separated text file.
if(!is.null(args$JSON) && !is.na(args$JSON) && is.character(args$JSON)){
  full_dirs <- unlist(read.delim(args$JSON, sep = "\n", header = FALSE))
  filepaths <- c(list.files(full_dirs, pattern = "\\.json", full.names = TRUE, recursive = TRUE),
                 grep("\\.json", full_dirs, value = TRUE))
  
  if(length(filepaths) > 0) {
    tbl0 <- simple_appender(filepaths, tbl0)
  }
  
} else {
  print("No additional JSONs to be added.")
}

#########################
#### R CONFIGURATION ####
#########################
#Loads variable configuration file. This file has settings for independent, dependent, and covariate variables;
#alias assignment if a variable name change is desired by the user; spectral and poincare plots selected by the user;
#maximum and minimum settings for the y-axis as designated by the user;                            
#and transformations chosen by the user for data in the main loop.                            
if((!is.null(args$R_config)) && (!is.na(args$R_config)) && (args$R_config != "None")) {
  print("Loading new variable configuration")
  var_names <- read.csv(args$R_config, stringsAsFactors=FALSE, na.strings = c("NA", "", " "))
  #Convert to names without units.
  var_names$With_units <- var_names$Alias
  var_names$Alias <- sapply(var_names$With_units, wu_convert)
  
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
#Loads graph configuration file. This file has settings for graphing in the main loop;
#xvar, pointdodge, facet1 and facet2; and ordering of variables to be graphed in the main loop.
#Orders set for the main loop are also applied to the optional graphs where the same variables
#are chosen.                            
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
#Loads optional graph configuration file. This file has settings for all optional graphs added by the user;
#and apnea and sigh featured breathing graphs, if selected for production by the user.
if((!is.null(args$Foxtrot)) && (!is.na(args$Foxtrot)) && (args$Foxtrot != "None")) {
  print("Loading new optional graph settings")
  other_config <- read.csv(args$Foxtrot, stringsAsFactors = FALSE, na.strings = c("", " ", "NA"))
} else {
  print("Keeping old optional graph configuration")
}

##########################
## Character Conversion ##
##########################
# Truncates very long category names in preparation for plotting.
for(ii in 1:ncol(tbl0)){
  if(typeof(tbl0[[ii]]) == "character"){
    tbl0[[ii]] <- str_trunc(tbl0[[ii]], 25, side = "center", ellipsis = "___")
  }
}

rm(mod_res)
rm(mod_res_list)
rm(tukey_res_list)
rm(graph_df)

save_atp <- try(save.image(file=paste0(args$Output, "/myEnv_",format(Sys.time(),'%Y%m%d_%H%M%S'),".RData")))
if(class(save_atp) == "try-error") {save.image(file=paste0("./myEnv_", format(Sys.time(),'%Y%m%d_%H%M%S'),".RData"))}

###########################
##REMAINING STAGG SCRIPTS##
###########################
# Designates location and names of the following R source codes to run after the completion of this script.
setwd(starting_wd)
source(args$Stat)
source(args$Makegraph)
source(args$Bodytemp)
