# library(gridExtra)
# library(data.table)

# Breath filter
cPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")
# other_config <- read.csv("/D/Resp/StaGG/V0_4/Other_config/Other_config1.csv", stringsAsFactors = FALSE, na.strings = c("", " ", "NA"))
sighs <- FALSE
apneas <- FALSE

# Runs the statistical modeling when mixed effects is not appropriate.
## Inputs:
### resp_var: character string, name of dependent variable.
### inter_vars: character vector, names of independent variables.
### cov_vars: character vector, names of covariates.
### run_data: data frame, data to fit model on
### inc_filter: boolean, whether breath inclusion filter should be used.
## Outputs (saved in list):
### rel_comp: data frame, pairwise comparison results for biologically relevant comparisons
### lm: data frame, coefficient estimates from the model for each of the interaction groups
stat_run_other <- function(resp_var, inter_vars, cov_vars, run_data, inc_filt = FALSE){
  
  # Removes rows with NAs and breath inclusion filter.
  if(inc_filt){
    run_data <- run_data %>% drop_na(any_of(inter_vars)) %>% dplyr::filter(Breath_Inclusion_Filter == 1)
  } else {
    run_data <- run_data %>% drop_na(any_of(inter_vars))
  }
  
  # Remove special characters and spaces in interaction variables categories. Necessary for relevant category finding below.
  # Should be processed in graph generator as well.
  for(vv in inter_vars){
    if(typeof(run_data[[vv]]) == "character"){
      run_data[[vv]] <- run_data[[vv]] %>% str_replace_all("[[:punct:]]", "") %>% str_replace_all(" ", "")
      run_data[[vv]] <- sapply(run_data[[vv]], X_num)
    }
  }
  
  return_values <- list()
  # Create interaction variable string
  interact_string <- paste0("run_data$interact <- with(run_data, interaction(", paste(inter_vars, collapse = ", "), "))")
  eval(parse(text = interact_string))
  # Create covariates
  covar_formula_string <- paste(c(1, cov_vars), collapse = "+")
  # Create full formula string for modeling.
  form <- as.formula(paste0(resp_var, " ~ interact + ", covar_formula_string))
  
  # Run model
  temp_mod <- lm(form, data = run_data)
  
  # Create all relevant comparisons for pairwise comparison testing.
  ## Find all interaction groups in model.
  all_names <- names(coef(temp_mod)) %>% str_replace_all("interact", "")
  ## Create all possible pairwise comparisons.
  comb_list <- c()
  for(rr in 2:(length(all_names) - 1)){
    for(ss in (rr+1):length(all_names)){
      comb_list <- c(comb_list, paste0(all_names[rr], " - ", all_names[ss]))
    }
  }
  
  ## Keep only biologically relevant pairwise comparisons
  ## I.e., where there is only one difference between two interaction variables among all variables that comprise them.
  comparison_names <- lapply(strsplit(comb_list, "-"), trimws)
  row_mismatches <- rep(NA, length(comparison_names))
  for(jj in 1:length(comparison_names)){
    comp_row <- strsplit(comparison_names[[jj]], split = "\\.")
    row_mismatches[jj] <- sum(comp_row[[1]] != comp_row[[2]])
  }
  ## Make names of biologically relevant comparisons for glht function
  comp_list <- comb_list[which(row_mismatches == 1)]
  ## Create output table
  for(qq in 1:length(comp_list)){
    comp_list[qq] <- paste0(comp_list[qq], " = 0")
  }
  
  ## Run model, save tables
  temp_tukey <- glht(temp_mod , linfct = mcp(interact = comp_list))
  vt <- summary(temp_tukey)$test
  mytest <- cbind(vt$coefficients, vt$sigma, vt$tstat, vt$pvalues)
  error <- attr(vt$pvalues, "error")
  pname <- switch(temp_tukey$alternativ,
                  less=paste("Pr(<", ifelse(temp_tukey$df == 0, "z", "t"), ")", sep = ""),
                  greater=paste("Pr(>", ifelse(temp_tukey$df == 0, "z", "t"), ")", sep = ""),
                  two.sided=paste("Pr(>|", ifelse(temp_tukey$df == 0, "z", "t"), "|)", sep = ""))
  colnames(mytest) <- c("Estimate", "Std. Error", ifelse(temp_tukey$df == 0, "z value", "t value"), pname)
  
  vttukey <- as.data.frame(xtable(mytest))
  colnames(vttukey) <- c("Estimate", "StdError", "zvalue", "pvalue")
  
  # Create return values
  return_values$rel_comp <- vttukey
  return_values$lm <- summary(temp_mod)$coef
  
  return(return_values)
}

#################################
####### THE LOOP ################
#################################

# Iterate through each of the rows in the config file.
## Create the desired plot for each row
if(nrow(other_config) > 0){
  print("Making optional graphs")
  for(ii in 1:nrow(other_config)){
    print((paste0("Making optional plot ", ii, "/", nrow(other_config))))
    other_config_row <- other_config[ii, ]
    other_config_row <- other_config_row[which(!is.na(other_config_row))]
    
    # Tags for specific sets of plots.
    if(is.null(other_config_row$Graph)) {
      next
    }
    
    if(other_config_row$Graph == "Sighs") {
      sighs <- TRUE
      next
    } 
    if(other_config_row$Graph == "Apneas") {
      apneas <- TRUE
      next
    }
    
    
    # Set graphing variables
    ocr2_wu <- c(other_config_row$Variable,
                 ifelse(is.null(other_config_row$Xvar), "", other_config_row$Xvar),
                 ifelse(is.null(other_config_row$Pointdodge), "", other_config_row$Pointdodge),
                 ifelse(is.null(other_config_row$Facet1), "", other_config_row$Facet1),
                 ifelse(is.null(other_config_row$Facet2), "", other_config_row$Facet2))
    names(ocr2_wu) <- c("Resp", "Xvar", "Pointdodge", "Facet1", "Facet2")
    
    # Get names of variables without units for internal usage.
    ocr2 <- sapply(ocr2_wu, wu_convert)
    names(ocr2) <- c("Resp", "Xvar", "Pointdodge", "Facet1", "Facet2")
    
    # Checks on user settings
    for(jj in ocr2[-1]){
      if(typeof(tbl0[[jj]]) == "numeric"){
        tbl0[[jj]] <- as.character(tbl0[[jj]])
      }
      if(length(unique(tbl0[[jj]])) > 8) {
        warning(paste0("Optional graphing variable ", jj, 
                     " has more than 8 categories; your graphs may become illegible. Is this a numeric variable"))
      }
    }
    
    # Whether to use the breath inclusion filter
    if((!is.null(other_config_row$Inclusion)) && (other_config_row$Inclusion == 0)){
      inclusion_filter <- FALSE
    } else {
      inclusion_filter <- TRUE
    }
    
    # Optional y-axis settings
    if((!is.null(other_config_row$ymin))) {
      ymins <- as.numeric(other_config_row$ymin)
    } else {
      ymins <- NA
    }
    if((!is.null(other_config_row$ymax))) {
      ymaxes <- as.numeric(other_config_row$ymax)
    } else {
      ymaxes <- NA
    }
    
    #######################################################
    # Body weight
    if(ocr2["Resp"] == "Weight") {
      
      #Gathers alias names of data columnns that contain the body weight values the user wishes to graph.
      bw_vars <- c(var_names$Alias[which(var_names$Body.Weight == 1)])
      
      if(length(bw_vars) == 0) {
        if("Weight" %in% var_names$Alias) {
          bw_vars <- "Weight"
        } else {
          print("No weight variables to plot.")
          next
        }
      }
      
      # Set graphing variables as a vector.
      box_vars <- c(ocr2["Xvar"], ocr2["Pointdodge"], ocr2["Facet1"], ocr2["Facet2"])
      box_vars <- box_vars[box_vars != ""]
      if(length(box_vars) == 0){ next }
      names(box_vars) <- NULL
      
      # Check user settings
      if((!is.null(other_config_row$Independent)) && (!is.na(other_config_row$Independent))){
        for(jj in c(unlist(strsplit(other_config_row$Independent, "@")) %>% sapply(wu_convert))){
          if(typeof(tbl0[[jj]]) == "numeric"){
            tbl0[[jj]] <- as.character(tbl0[[jj]])
          }
          if(length(unique(tbl0[[jj]])) == 1){
            warning(paste0("Independent variable ", jj, " has only one unique value. Results may be unreliable."))
          }
          if(length(unique(tbl0[[jj]])) > 20){
            warning(paste0("Independent variable ", jj, 
                           " has many unique values; this may cause memory issues. Should this be a covariate?"))
          }
        }
      }
      
      if((!is.null(other_config_row$Covariate)) && (!is.na(other_config_row$Covariate))){
        for(jj in c(unlist(strsplit(other_config_row$Covariate, "@")) %>% sapply(wu_convert))){
          if(length(unique(tbl0[[jj]])) == 1){
            warning(paste0("Covariate ", jj, " has only one unique value. Results may be unreliable."))
          }
        }
      }
      
      # Build stat modeling variable vector.
      if((!is.null(other_config_row$Independent)) && (!is.na(other_config_row$Independent))){
        other_inter_vars <- unique(c(box_vars, unlist(strsplit(other_config_row$Independent, "@")) %>% sapply(wu_convert)))
      } else {
        other_inter_vars <- box_vars
      }
      if((!is.null(other_config_row$Covariate)) && (!is.na(other_config_row$Covariate))){
        other_covars <- unique(unlist(strsplit(other_config_row$Covariate, "@")) %>% sapply(wu_convert))
      } else {
        other_covars <- character(0)
      }
      
      # Organizes data collected above for graphing.
      other_df <- tbl0 %>%
        dplyr::group_by_at(c(other_inter_vars, other_covars, "MUID")) %>%
        dplyr::summarise_at(bw_vars, mean, na.rm = TRUE) %>%
        dplyr::ungroup()
      other_graph_df <- tbl0 %>%
        dplyr::group_by_at(c(box_vars, "MUID")) %>%
        dplyr::summarise_at(bw_vars, mean, na.rm = TRUE) %>%
        dplyr::ungroup()
      
      # Check that variables are factors; set in order of appearance in data.
      for(jj in box_vars){
        other_graph_df[[jj]] <- factor(other_graph_df[[jj]], levels = unique(tbl0[[jj]]))
      }
      
      graph_file <- paste0("BodyWeight_", other_config_row$Graph, args$I)
      
      # Assumes weight is a mouse-level measurement.
      if(length(unique(other_df$MUID)) == nrow(other_df)){
        other_mod_res <- stat_run_other(bw_vars, other_inter_vars, other_covars, other_df, FALSE)
      } else {
        other_mod_res <- stat_run(bw_vars, other_inter_vars, other_covars, other_df, FALSE)
      }
      
      # Make graph + save
      graph_make(bw_vars, as.character(ocr2["Xvar"]), as.character(ocr2["Pointdodge"]), 
                 as.character(ocr2["Facet1"]), as.character(ocr2["Facet2"]), other_graph_df, 
                 other_mod_res$rel_comp, box_vars, graph_file, other = TRUE, 
                 "Weight", as.character(ocr2_wu["Xvar"]), as.character(ocr2_wu["Pointdodge"]),
                 ymins, ymaxes)
      
    #######################################################
    # Body Temp  
    } else if(ocr2["Resp"] == "Temperature") {
      
      #CURRENTLY IGNORES ANY XVAR INPUT
      #Gathers alias names of data columns that contain the body temperature values the user wishes to graph.
      bt_vars <- c((var_names$Alias[which(var_names$Start.Body.Temp == 1)]), 
                   (var_names$Alias[which(var_names$Mid.Body.Temp == 1)]), 
                   (var_names$Alias[which(var_names$End.Body.Temp == 1)]), 
                   (var_names$Alias[which(var_names$Post.Body.Temp == 1)]))
      
      if(length(bt_vars) == 0) {
        print("No temperature variables to plot.")
        next
      }
      
      # Set graphing variables as a vector.
      temp_vars <- c(ocr2["Pointdodge"], ocr2["Facet1"], ocr2["Facet2"])
      temp_vars <- temp_vars[temp_vars != ""]
      names(temp_vars) <- NULL
      
      # Check user settings
      ## Print warnings if possible issues.
      if((!is.null(other_config_row$Independent)) && (!is.na(other_config_row$Independent))){
        for(jj in c(unlist(strsplit(other_config_row$Independent, "@")) %>% sapply(wu_convert))){
          if(typeof(tbl0[[jj]]) == "numeric"){
            tbl0[[jj]] <- as.character(tbl0[[jj]])
          }
          if(length(unique(tbl0[[jj]])) == 1){
            warning(paste0("Independent variable ", jj, " has only one unique value. Results may be unreliable."))
          }
          if(length(unique(tbl0[[jj]])) > 20){
            warning(paste0("Independent variable ", jj, 
                           " has many unique values; this may cause memory issues. Should this be a covariate?"))
          }
        }
      }
      if((!is.null(other_config_row$Covariate)) && (!is.na(other_config_row$Covariate))){
        for(jj in c(unlist(strsplit(other_config_row$Covariate, "@")) %>% sapply(wu_convert))){
          if(length(unique(tbl0[[jj]])) == 1){
            warning(paste0("Covariate ", jj, " has only one unique value. Results may be unreliable."))
          }
        }
      }
      
      # Build stat modeling variable vector.
      if((!is.null(other_config_row$Independent)) && (!is.na(other_config_row$Independent))){
        other_inter_vars <- unique(c(temp_vars, unlist(strsplit(other_config_row$Independent, "@")) %>% sapply(wu_convert)))
      } else {
        other_inter_vars <- temp_vars
      }
      if((!is.null(other_config_row$Covariate)) && (!is.na(other_config_row$Covariate))){
        other_covars <- unique(unlist(strsplit(other_config_row$Covariate, "@")) %>% sapply(wu_convert))
      } else {
        other_covars <- character(0)
      }
      
      #Organizes data collected above for graphing.
      bodytemp_df <- tbl0 %>%
        dplyr::group_by_at(c(other_inter_vars, other_covars, "MUID")) %>%
        dplyr::summarise_at(bt_vars, mean, na.rm = TRUE) %>%
        dplyr::ungroup()
      bodytemp_graph_df <- tbl0 %>%
        dplyr::group_by_at(c(temp_vars, "MUID")) %>%
        dplyr::summarise_at(bt_vars, mean, na.rm = TRUE) %>%
        dplyr::ungroup()
      
      #Organizes data collected above for graphing.
      melt_bt_df <- reshape2::melt(bodytemp_df, id=c(temp_vars, "MUID"))
      melt_bt_graph_df <- reshape2::melt(bodytemp_graph_df, id=c(temp_vars, "MUID"))
      
      # Set ordering of body temp variables.
      levels(melt_bt_graph_df$variable) <- c((var_names$Alias[which(var_names$Start.Body.Temp == 1)]), 
                                             (var_names$Alias[which(var_names$Mid.Body.Temp == 1)]), 
                                             (var_names$Alias[which(var_names$End.Body.Temp == 1)]), 
                                             (var_names$Alias[which(var_names$Post.Body.Temp == 1)]))
      levels(melt_bt_df$variable) <- c((var_names$Alias[which(var_names$Start.Body.Temp == 1)]), 
                                             (var_names$Alias[which(var_names$Mid.Body.Temp == 1)]), 
                                             (var_names$Alias[which(var_names$End.Body.Temp == 1)]), 
                                             (var_names$Alias[which(var_names$Post.Body.Temp == 1)]))
      
      # Check that variables are factors; set in order of appearance in data.
      for(jj in temp_vars){
        melt_bt_graph_df[[jj]] <- factor(melt_bt_graph_df[[jj]], levels = unique(tbl0[[jj]]))
        melt_bt_df[[jj]] <- factor(melt_bt_df[[jj]], levels = unique(tbl0[[jj]]))
      }
      
      # Rename variables
      setnames(melt_bt_graph_df, old = c("value", "variable"), new = c("Temp", "State"), skip_absent = TRUE)
      temp_vars <- c("State", temp_vars)
      
      graph_file <- paste0("BodyTemp_", other_config_row$Graph, args$I)
      
      # Assumes temperature is a mouse-level measurement.
      other_mod_res <- stat_run("Temp", other_inter_vars, other_covars, melt_bt_df, FALSE)
      
      # Make graph + save
      graph_make("Temp", "State", as.character(ocr2["Pointdodge"]), 
                 as.character(ocr2["Facet1"]), as.character(ocr2["Facet2"]), melt_bt_graph_df, 
                 other_mod_res$rel_comp, temp_vars, graph_file, other = TRUE,
                 "Temperature", "Time", as.character(ocr2_wu["Pointdodge"]),
                 ymins, ymaxes)
      
    #######################################################
    # Custom  
    } else {
      if(ocr2["Resp"] %in% colnames(tbl0)) {
        
        # Set graphing variables as a vector.
        box_vars <- c(ocr2["Xvar"], ocr2["Pointdodge"], ocr2["Facet1"], ocr2["Facet2"])
        box_vars <- box_vars[box_vars != ""]
        if(length(box_vars) == 0){ next }
        names(box_vars) <- NULL
        
        # Check user settings
        ## Print warnings if possible issues.
        if((!is.null(other_config_row$Independent)) && (!is.na(other_config_row$Independent))){
          for(jj in c(unlist(strsplit(other_config_row$Independent, "@")) %>% sapply(wu_convert))){
            if(typeof(tbl0[[jj]]) == "numeric"){
              tbl0[[jj]] <- as.character(tbl0[[jj]])
            }
            if(length(unique(tbl0[[jj]])) == 1){
              warning(paste0("Independent variable ", jj, " has only one unique value. Results may be unreliable."))
            }
            if(length(unique(tbl0[[jj]])) > 20){
              warning(paste0("Independent variable ", jj, 
                             " has many unique values; this may cause memory issues. Should this be a covariate?"))
            }
          }
        }
        if((!is.null(other_config_row$Covariate)) && (!is.na(other_config_row$Covariate))){
          for(jj in c(unlist(strsplit(other_config_row$Covariate, "@")) %>% sapply(wu_convert))){
            if(length(unique(tbl0[[jj]])) == 1){
              warning(paste0("Covariate ", jj, " has only one unique value. Results may be unreliable."))
            }
          }
        }

        # Build stat modeling variable vector.
        if((!is.null(other_config_row$Independent)) && (!is.na(other_config_row$Independent))){
          other_inter_vars <- unique(c(box_vars, unlist(strsplit(other_config_row$Independent, "@")) %>% sapply(wu_convert)))
        } else {
          other_inter_vars <- box_vars
        }
        if((!is.null(other_config_row$Covariate)) && (!is.na(other_config_row$Covariate))){
          other_covars <- unique(unlist(strsplit(other_config_row$Covariate, "@")) %>% sapply(wu_convert))
        } else {
          other_covars <- character(0)
        }
        
        # Organizes data collected above for graphing.
        if(inclusion_filter) {
          ## Data frame for stat modeling
          other_df <- tbl0 %>%
            dplyr::group_by_at(c(other_inter_vars, other_covars, "MUID")) %>%
            dplyr::filter(Breath_Inclusion_Filter == 1) %>%
            #dplyr::summarise_at(as.character(ocr2["Resp"]), mean, na.rm = TRUE) %>%
            dplyr::ungroup()
          ## Data frame for plotting
          other_graph_df <- tbl0 %>%
            dplyr::filter(Breath_Inclusion_Filter == 1) %>%
            dplyr::group_by_at(c(box_vars, "MUID")) %>%
            dplyr::summarise_at(as.character(ocr2["Resp"]), mean, na.rm = TRUE) %>%
            dplyr::ungroup()
        } else {
          ## Data frame for stat modeling
          other_df <- tbl0 %>%
            dplyr::group_by_at(c(other_inter_vars, other_covars, "MUID")) %>%
            #dplyr::summarise_at(as.character(ocr2["Resp"]), mean, na.rm = TRUE) %>%
            dplyr::ungroup()
          ## Data frame for plotting
          other_graph_df <- tbl0 %>%
            dplyr::group_by_at(c(box_vars, "MUID")) %>%
            dplyr::summarise_at(as.character(ocr2["Resp"]), mean, na.rm = TRUE) %>%
            dplyr::ungroup()
        }
        
        # Check that variables are factors; set in order of appearance in data.
        for(jj in box_vars){
          other_graph_df[[jj]] <- factor(other_graph_df[[jj]], levels = unique(tbl0[[jj]]))
        }
        
        graph_file <- paste0(other_config_row$Variable, "_", other_config_row$Graph, args$I)
        
        # Runs stat modeling
        # Assumes that each individual observation is relevant (and not mouse-level statistic.)
        if(length(unique(other_df$MUID)) == nrow(other_df)){
          other_mod_res <- stat_run_other(as.character(ocr2["Resp"]), other_inter_vars, other_covars, other_df, FALSE)
        } else {
          other_mod_res <- stat_run(as.character(ocr2["Resp"]), other_inter_vars, other_covars, other_df, FALSE)
        }
        
        # Make graph + save
        graph_make(as.character(ocr2["Resp"]), as.character(ocr2["Xvar"]), as.character(ocr2["Pointdodge"]), 
                   as.character(ocr2["Facet1"]), as.character(ocr2["Facet2"]), other_graph_df, 
                   other_mod_res$rel_comp, box_vars, graph_file, other = TRUE,
                   as.character(ocr2_wu["Resp"]), as.character(ocr2_wu["Xvar"]), as.character(ocr2_wu["Pointdodge"]),
                   ymins, ymaxes)
        
      } else {
        ## If the response variable doesn't exist, skip.
        print(paste0("Unable to make graph ", other_config_row$Graph, "; unexpected response variable."))
        next
      }
    }
    
  }
  
}



#######################################
##### Apneas & Sighs ##################
#######################################

# Functionality to make graphs for sigh and apnea rates.
if(sighs || apneas){
  print("Making apnea and sigh graphs")
  tbl0$measure_breaks <- as.logical(c(FALSE, tbl0$Mouse_And_Session_ID[1:(nrow(tbl0) - 1)] != 
                                        tbl0$Mouse_And_Session_ID[2:(nrow(tbl0))]))
  
  # Set graphing variables as a vector.
  box_vars <- c(xvar, pointdodge, facet1, facet2)
  box_vars <- box_vars[box_vars != ""]
  
  # Summarize data by mouse for plotting.
  ## Find total measurement time for each interaction group + mouse.
  timetab <- tbl0 %>%
    dplyr::filter(!measure_breaks) %>%
    dplyr::group_by_at(c(box_vars, "MUID")) %>%
    dplyr::summarise_at(var_names$Alias[which(var_names$Column == "Breath_Cycle_Duration")], sum, na.rm = TRUE)
  colnames(timetab)[ncol(timetab)] <- "measuretime"  
  ## Find number of sighs/apneas for each interaction group + mouse.
  eventtab <- tbl0 %>%
    dplyr::filter(!measure_breaks) %>%
    dplyr::group_by_at(c(box_vars, "MUID")) %>%
    dplyr::summarise(sighs = sum(Sigh), apneas = sum(Apnea))
  ## Join tables to calculate rates.
  eventtab_join <- inner_join(eventtab, timetab, by = c(box_vars, "MUID")) %>%
    mutate(SighRate = sighs/measuretime*60, ApneaRate = apneas/measuretime*60)
  
  # By default, set categories in order of appearance in data.
  for(ii in box_vars){
    eventtab_join[[ii]] <- factor(eventtab_join[[ii]], levels = unique(tbl0[-c(measure_breaks), ][[ii]]))
  }
  
  # Set label + internal variable names.
  ## Depending on if sighs and/or apneas are desired.
  r_vars <- c()
  r_vars_wu <- c()
  if(sighs){
    r_vars <- c(r_vars, "SighRate")
    r_vars_wu <- c(r_vars_wu, "Sigh Rate (1/min)")
  }
  if(apneas){
    r_vars <- c(r_vars, "ApneaRate")
    r_vars_wu <- c(r_vars_wu, "Apnea Rate (1/min)")
  }
  
  # Loop to make sighs + apneas graphs.
  for(ii in 1:length(r_vars)){
    graph_file <- paste0(r_vars[ii],args$I)
    
    # Stat modeling, calculated ONLY using graphing variables as independent variables.
    other_mod_res <- stat_run(r_vars[ii], box_vars, character(0), eventtab_join, FALSE)
    
    # Make graph + save
    graph_make(r_vars[ii], xvar, pointdodge, facet1, facet2, eventtab_join, 
               other_mod_res$rel_comp, box_vars, graph_file, other = TRUE,
               r_vars_wu[ii], xvar_wu, pointdodge_wu)
  }
}

#######################################
########## Poincare plots #############
#######################################

# Function to make poincare plots.
## Inputs:
### resp_var: character string, name of dependent variable.
### graph_data: data frame, data used for graphing.
### xvar: character string, variable to separate data to different plots by categories of corresponding variable.
### pointdodge: character string, variable to separate points to different colors.
### facet1: character string, variable for row panels.
### facet2: character string, variable for column panels.
### pointdodge_name: character string, desired legend title for color.
### inclusion_filter: boolean, whether to exclude points by the breath filter.
## Outputs:
### Saves generated plot; otherwise no return value.
poincare_graph <- function(resp_var, graph_data, xvar, pointdodge, facet1, 
                           facet2, pointdodge_name = "", inclusion_filter = TRUE) {
  
  if(!is.numeric(graph_data[[resp_var]])){
    print(paste0("Poincare plot variable '", resp_var, "' not numeric."))
    return()
  }
  
  # Create lead/lag data for plotting
  poincare_df <- data.frame(lag = graph_data[[resp_var]][-nrow(graph_data)], 
                            lead = graph_data[[resp_var]][-1],
                            Breath_Inclusion_Filter = graph_data$Breath_Inclusion_Filter[-nrow(graph_data)])
  
  # Settings for graphing variables
  ## Point color
  if(pointdodge != ""){
    poincare_df$pc <- factor(graph_data[[pointdodge]][-nrow(graph_data)], 
                             levels = unique(graph_data[[pointdodge]]))
    pointdodge_g <- "pc"
  } else {
    pointdodge_g <- NULL
  }
  
  ## Rowpanels.
  if(facet1 != ""){
    poincare_df$facet1 <- factor(graph_data[[facet1]][-nrow(graph_data)], 
                                 levels = unique(graph_data[[facet1]]))
    facet1_g <- "facet1"
  } else {
    facet1_g <- "."
  }
  
  ## Column panels.
  if(facet2 != ""){
    poincare_df$facet2 <- factor(graph_data[[facet2]][-nrow(graph_data)], 
                                 levels = unique(graph_data[[facet2]]))
    facet2_g <- "facet2"
  } else {
    facet2_g <- "."
  }
  
  ## Different files
  if(xvar != ""){
    if(is.numeric(graph_data[[xvar]])){
      print(paste0("Invalid Xvar for poincare plot ", xvar))
      next
    }
    
    poincare_df$xvar <- factor(graph_data[[xvar]][-nrow(graph_data)], 
                               levels = unique(graph_data[[xvar]]))
  }
  
  # Break up non-sequential observations
  measure_breaks <- as.numeric(which(graph_data$Mouse_And_Session_ID[1:(nrow(graph_data) - 1)] != 
                                       graph_data$Mouse_And_Session_ID[2:(nrow(graph_data))]))
  if(length(measure_breaks) != 0){
    poincare_df <- poincare_df[-c(measure_breaks), ]
  }
  
  # Are filtered breaths included?
  if(inclusion_filter){
    poincare_df <- poincare_df %>% dplyr::filter(Breath_Inclusion_Filter == 1)
  } 
  
  form_string <- as.formula(paste0(facet2_g, " ~ ", facet1_g))
  
  # Currently no functionality for custom axis ranges.
  if(xvar != ""){
    for(ll in unique(poincare_df[["xvar"]])) {
      poincare_df_sub <- poincare_df[which(poincare_df[["xvar"]] == ll),]
      
      # Make graph + save
      p <- ggplot() +
        geom_point(aes_string(x = "lag", y = "lead", color = pointdodge_g), data = poincare_df_sub) +
        geom_abline(slope = 1, intercept = 0) +
        facet_grid(form_string) + 
        scale_color_manual(values = cPalette) +
        labs(x = "T", y = "T+1", color = pointdodge_wu) +
        theme_few() 
      
      graph_file <- str_replace_all(paste0("Poincare_", resp_var, "_", ll, args$I), " ", "")
      ggsave(graph_file, plot = p, path = args$Output, width = 17.5, height = 17.5, units = "cm")
    }
    
  } else {
    # Make graph + save
    p <- ggplot() +
      geom_point(aes_string(x = "lag", y = "lead", color = pointdodge_g), data = poincare_df) +
      geom_abline(slope = 1, intercept = 0) +
      facet_grid(form_string) + 
      scale_color_manual(values = cPalette) +
      labs(x = "T", y = "T+1", color = pointdodge_wu) +
      theme_few() 
    
    graph_file <- paste0("Poincare_", resp_var, args$I)
    ggsave(graph_file, plot = p, path = args$Output, width = 17.5, height = 17.5, units = "cm")
  }
  return()
}

# Run poincare graph function
if((!is.na(poincare_vars)) && (length(poincare_vars) != 0)){
  for(ii in 1:length(poincare_vars)){
    print((paste0("Making Poincare plot ", ii, "/", length(poincare_vars))))
    poincare_graph(poincare_vars[ii], tbl0, xvar, pointdodge, facet1, 
                   facet2, pointdodge_wu)
  }
}

#######################################
##### Power spectral plots ############
#######################################

# Function to make Spectral plots.
## Input:
### resp_var: character string, name of dependent variable.
### graph_data: data frame, data used for graphing.
### pointdodge: character string, variable to separate different plots.
### inclusion_filter: boolean, whether to exclude points by the breath filter.
## Outputs:
### Saves generated plot; otherwise no return value.
spec_graph <- function(resp_var, graph_data, pointdodge) {
  
  # Calculate range of frequencies to graph.
  avg_breath_len <- mean(graph_data[["Breath_Cycle_Duration"]], na.rm = TRUE)
  max_hz <- min(max(2, floor(60/avg_breath_len)), min(table(graph_data[[pointdodge]])) / 2)
  if(is.nan(avg_breath_len)){avg_breath_len <- 0.15}
  
  # If pointdodge is specified, create separate plots per category.
  if(pointdodge != ""){
    psd_list <- list()
    for(vv in unique(graph_data[[pointdodge]])){
      # Create subdata; remove NAs
      graph_data_sub <- graph_data[which(graph_data[[pointdodge]] == vv), ]
      graph_data_sub <- graph_data_sub[which(!is.na(graph_data_sub[[resp_var]])), ]
      # Calculate spectral
      psd_list[[vv]] <- Mod(fft(graph_data_sub[[resp_var]]))[2:max_hz] * 2
    }
    
    # Turn results to data frame for plotting
    psd_df <-  reshape2::melt(as.data.frame(psd_list))
    psd_df$tt <- rep(2:max_hz, length(unique(graph_data[[pointdodge]])))
    
    # Make graph + save
    psd_p <- ggplot(data = psd_df) +
      geom_path(aes(x = tt, y = value)) +
      facet_grid(rows = vars(variable), scales = "free_y") +
      labs(x = "Hz", y = "Magnitude") +
      theme_bw()
    
    graph_file <- paste0("Spectral_", resp_var, "_", pointdodge, args$I)
    ggsave(graph_file, plot = psd_p, path = args$Output, width = 6, height = 2 * length(unique(graph_data[[pointdodge]])), units = "in")
    
  } else {
    # Remove NAs
    graph_data_sub <- graph_data[which(!is.na(graph_data[[resp_var]])), ]
    # Calculate spectral
    psd <- Mod(fft(graph_data_sub[[resp_var]]))[2:max_hz] * 2
    
    # Make graph + save
    psd_p <- ggplot() +
      geom_path(aes(x = 2:max_hz, y = psd[2:max_hz])) +
      labs(x = "Hz", y = "Magnitude") +
      theme_bw()
    
    graph_file <- paste0("Spectral_", resp_var, args$I)
    ggsave(graph_file, plot = psd_p, path = args$Output, width = 6, height = 2, units = "in")
  }
  return()
}

# Run spectral graph function
if((!is.na(spec_vars)) && (length(spec_vars) != 0)){
  for(ii in 1:length(spec_vars)){
    print((paste0("Making spectral plot ", ii, "/", length(spec_vars))))
    spec_graph(spec_vars[ii], tbl0, pointdodge)
  }
}


#######################################
##### Summary RMD #####################
#######################################

##Runs the R markdown code and saves to the output directory.
print("Making summary HTML")

# Assumes first that args$Sum is a directory containing Summary.Rmd
rmd_file <- list.files(path = args$Sum, pattern = "Summary\\.Rmd", 
                       all.files = TRUE, full.names = TRUE, 
                       recursive = TRUE, ignore.case = TRUE)

# If not, see if args$Sum is pointing directly to the Summary.Rmd file 
if(length(rmd_file) == 0){
  rmd_file <- args$Sum
}

# Render RMD file.
html_try <- try(rmarkdown::render(rmd_file, output_dir = args$Output))

# If there is an error, 
if(class(html_try) == "try-error"){
  print("No Summary Rmd file found in specified location.")
}
