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
#This script brings in settings and options for graphs that are not part of the main loop.
# These graphs are optional to the user, but allow the user more flexibility to graph variables in different
##ways or new variables that aren't respiratory outcomes. 

# Color palette for use in graphs
cPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")

# Default settings
sighs <- FALSE
apneas <- FALSE

###############################################
##ALTERNATIVE STATS WHEN LMER NOT APPROPRIATE##
###############################################
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
  
  # Basic stats 
  b_stat_data <- run_data %>%
    group_by_at(c(inter_vars)) %>%
    dplyr::summarise_at(resp_var, list(mean, sd), na.rm = TRUE) %>%
    ungroup() %>% na.omit()
  
  colnames(b_stat_data)[ncol(b_stat_data) - 1] <- "Mean"
  colnames(b_stat_data)[ncol(b_stat_data)] <- "Std.Dev."
  
  # Remove special characters and spaces in interaction variables categories. Necessary for relevant category finding below.
  # Should be processed in graph generator as well.
  for(vv in inter_vars){
    if(typeof(run_data[[vv]]) == "character"){
      run_data[[vv]] <- run_data[[vv]] %>% str_replace_all("[[:punct:]]", "") %>% str_replace_all(" ", "")
      run_data[[vv]] <- sapply(run_data[[vv]], X_num)
    }
  }
  
  # Create list for function output.
  return_values <- list()
  # Create interaction variable string
  interact_string <- paste0("run_data$interact <- with(run_data, interaction(", paste(inter_vars, collapse = ", "), "))")
  eval(parse(text = interact_string))
  # Create covariates
  covar_formula_string <- paste(c(0, cov_vars), collapse = "+")
  # Create full formula string for modeling.
  form <- as.formula(paste0(resp_var, " ~ interact + ", covar_formula_string))
  
  # Run model
  temp_mod <- lm(form, data = run_data)
  
  # Create all relevant comparisons for pairwise comparison testing.
  ## Find all interaction groups in model.
  all_names <- grep("interact", names(coef(temp_mod)), value = TRUE) %>% str_replace_all("interact", "")
  ## Create all possible pairwise comparisons.
  comb_list <- c()
  for(rr in 1:(length(all_names) - 1)){
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
  
  # Make residual plots
  ## Raw residual plot
  g1 <- ggplot() +
    geom_point(aes(x = fitted(temp_mod), y = resid(temp_mod))) +
    labs(x = "Fitted", y = "Residual", title = paste0("Residuals: ", resp_var, " ~ ", paste(inter_vars, collapse = "+ "))) + 
    geom_abline(slope = 0, intercept = 0) +
    theme_few() 
  
  ## Q-Q plot
  g2 <- ggplot() +
    geom_qq(aes(sample = resid(temp_mod))) +
    labs(x = "Empirical Quantile", y = "Theoretical Quantile", title = paste0("Q-Q: ", resp_var, " ~ ", paste(inter_vars, collapse = "+ "))) + 
    geom_qq_line(aes(sample = resid(temp_mod))) +
    theme_few() 
  
  # Create return values
  return_values$rel_comp <- vttukey
  return_values$lm <- summary(temp_mod)$coef
  return_values$residplot <- g1
  return_values$qqplot <- g2
  return_values$b_stat <- b_stat_data
  
  return(return_values)
}

#################################
####### THE LOOP ################
#################################

# Create the desired optional plot.
## Inputs:
### other_config_row: 1 row data frame, row of optional config.
### tbl0: data frame, full data set.
### var_names: data frame, R config file.
### graph_vars: data frame, graph config file.
### other_stat_dir: character string, location of optional stat output folder.
### dirtest: logical, whether default optional stat output folder was successfully created.
### xvar, pointdodge, facet1, facet2: main graphing loop variables. Used only for ordering factors as specified in the graph config file.
## Outputs:
### other_mod_res: statistics results used for the optional graphs.
optional_graph_maker <- function(other_config_row, tbl0, var_names, graph_vars, other_stat_dir, dirtest,
                                 xvar, pointdodge, facet1, facet2){
  
  graph_v <- c(xvar, pointdodge, facet1, facet2)
  graph_v <- graph_v[graph_v != ""]
  
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
  if(grepl("Weight", ocr2["Resp"])) {
    
    #Gathers alias names of data columns that contain the body weight values the user wishes to graph.
    bw_vars <- c(var_names$Alias[which(var_names$Body.Weight == 1)])
    
    if(length(bw_vars) == 0) {
      if("Weight" %in% var_names$Alias) {
        bw_vars <- "Weight"
      } else {
        stop("No weight variables to plot.")
      }
    }
    
    # Set graphing variables as a vector.
    box_vars <- c(ocr2["Xvar"], ocr2["Pointdodge"], ocr2["Facet1"], ocr2["Facet2"])
    box_vars <- box_vars[box_vars != ""]
    if(length(box_vars) == 0){ stop("Weight plot requires an independent variable.") }
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
    
    # Set order of categories in variables as specified by the user, if specified.
    regraph_vars <- box_vars[which(box_vars %in% graph_v)] 
    if(length(regraph_vars) != 0){
      other_graph_df <- graph_reorder(other_graph_df, regraph_vars, graph_vars, tbl0)
    }
    
    name_part <- str_replace_all(other_config_row$Graph, "[[:punct:]]", "")
    graph_file <- paste0("BodyWeight_", name_part, args$I) %>% str_replace_all(" ", "")
    
    # Assumes weight is a mouse-level measurement.
    if(length(unique(other_df$MUID)) == nrow(other_df)){
      other_mod_res <- stat_run_other(bw_vars, other_inter_vars, other_covars, other_df, FALSE)
    } else {
      other_mod_res <- stat_run(bw_vars, other_inter_vars, other_covars, other_df, FALSE)
    }
    
    # Make graph + save
    graph_make(bw_vars, as.character(ocr2["Xvar"]), as.character(ocr2["Pointdodge"]), 
               as.character(ocr2["Facet1"]), as.character(ocr2["Facet2"]), other_graph_df, 
               other_df, other_mod_res$rel_comp, box_vars, graph_file, other = TRUE, inc_filter = inclusion_filter,
               "Weight", as.character(ocr2_wu["Xvar"]), as.character(ocr2_wu["Pointdodge"]),
               ymins, ymaxes)
    
    ## Save residual plots
    if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
      if(args$I == ".svg"){
        svglite(paste0(args$Output, "/Residual_", other_config_row$Graph, args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(args$Output, "/QQ_", other_config_row$Graph, args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, path = args$Output)
        ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, path = args$Output)
      }
    } else {
      if(args$I == ".svg"){
        svglite(paste0(other_stat_dir, "/Residual_", other_config_row$Graph, args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(other_stat_dir, "/QQ_", other_config_row$Graph, args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
        ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
      }
    }
    
    #######################################################
    # Age graphs. NB: Requires a column specifically named "Age"
  } else if(grepl("Age", ocr2["Resp"])) {
    
    # Check if there is an Age column
    if("Age" %in% var_names$Alias) {
      age_vars <- "Age"
    } else {
      stop("No Age variable to plot.")
    }
    
    # Set graphing variables as a vector.
    box_vars <- c(ocr2["Xvar"], ocr2["Pointdodge"], ocr2["Facet1"], ocr2["Facet2"])
    box_vars <- box_vars[box_vars != ""]
    if(length(box_vars) == 0){  stop("Age plot requires an independent variable.") }
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
      dplyr::summarise_at(age_vars, mean, na.rm = TRUE) %>%
      dplyr::ungroup()
    other_graph_df <- tbl0 %>%
      dplyr::group_by_at(c(box_vars, "MUID")) %>%
      dplyr::summarise_at(age_vars, mean, na.rm = TRUE) %>%
      dplyr::ungroup()
    
    # Check that variables are factors; set in order of appearance in data.
    for(jj in box_vars){
      other_graph_df[[jj]] <- factor(other_graph_df[[jj]], levels = unique(tbl0[[jj]]))
    }
    
    # Set order of categories in variables as specified by the user, if specified.
    regraph_vars <- box_vars[which(box_vars %in% graph_v)] 
    if(length(regraph_vars) != 0){
      other_graph_df <- graph_reorder(other_graph_df, regraph_vars, graph_vars, tbl0)
    }
    
    name_part <- str_replace_all(other_config_row$Graph, "[[:punct:]]", "")
    graph_file <- paste0("Age_", name_part, args$I) %>% str_replace_all(" ", "")
    
    # Assumes weight is a mouse-level measurement.
    if(length(unique(other_df$MUID)) == nrow(other_df)){
      other_mod_res <- stat_run_other(age_vars, other_inter_vars, other_covars, other_df, FALSE)
    } else {
      other_mod_res <- stat_run(age_vars, other_inter_vars, other_covars, other_df, FALSE)
    }
    
    # Make graph + save
    graph_make(age_vars, as.character(ocr2["Xvar"]), as.character(ocr2["Pointdodge"]), 
               as.character(ocr2["Facet1"]), as.character(ocr2["Facet2"]), other_graph_df, 
               other_df, other_mod_res$rel_comp, box_vars, graph_file, other = TRUE, inc_filter = inclusion_filter,
               "Weight", as.character(ocr2_wu["Xvar"]), as.character(ocr2_wu["Pointdodge"]),
               ymins, ymaxes)
    
    ## Save residual plots
    if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
      if(args$I == ".svg"){
        svglite(paste0(args$Output, "/Residual_", other_config_row$Graph, args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(args$Output, "/QQ_", other_config_row$Graph, args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, path = args$Output)
        ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, path = args$Output)
      }
    } else {
      if(args$I == ".svg"){
        svglite(paste0(other_stat_dir, "/Residual_", other_config_row$Graph, args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(other_stat_dir, "/QQ_", other_config_row$Graph, args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
        ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
      }
    }
    
    #######################################################
    # Body Temp  
  } else if(grepl("Temperature", ocr2["Resp"])) {
    
    #CURRENTLY IGNORES ANY XVAR INPUT
    #Gathers alias names of data columns that contain the body temperature values the user wishes to graph.
    bt_vars_name <- c("Start_body_temperature", "Mid_body_temperature", 
                      "End_body_temperature", "post30_body_temperature")
    bt_vars <- bt_vars_name[which(bt_vars_name %in% names(tbl0))]
    
    if(length(bt_vars) == 0) {
      stop("No temperature variables to plot.")
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
    levels(melt_bt_graph_df$variable) <- bt_vars
    levels(melt_bt_df$variable) <- bt_vars
    
    # Check that variables are factors; set in order of appearance in data.
    for(jj in temp_vars){
      melt_bt_graph_df[[jj]] <- factor(melt_bt_graph_df[[jj]], levels = unique(tbl0[[jj]]))
      melt_bt_df[[jj]] <- factor(melt_bt_df[[jj]], levels = unique(tbl0[[jj]]))
    }
    
    # Rename variables
    setnames(melt_bt_graph_df, old = c("value", "variable"), new = c("Temp", "State"), skip_absent = TRUE)
    temp_vars <- c("State", temp_vars)
    
    # Set order of categories in variables as specified by the user, if specified.
    regraph_vars <- temp_vars[which(temp_vars %in% graph_v)] 
    if(length(regraph_vars) != 0){
      melt_bt_graph_df <- graph_reorder(melt_bt_graph_df, regraph_vars, graph_vars, tbl0)
    }
    
    name_part <- str_replace_all(other_config_row$Graph, "[[:punct:]]", "")
    graph_file <- paste0("BodyTemp_", name_part, args$I) %>% str_replace_all(" ", "")
    
    # Assumes temperature is a mouse-level measurement.
    other_mod_res <- stat_run("Temp", other_inter_vars, other_covars, melt_bt_df, FALSE)
    
    # Make graph + save
    graph_make("Temp", "State", as.character(ocr2["Pointdodge"]), 
               as.character(ocr2["Facet1"]), as.character(ocr2["Facet2"]), melt_bt_graph_df, 
               bodytemp_df, other_mod_res$rel_comp, temp_vars, graph_file, other = TRUE, inc_filter = inclusion_filter,
               "Temperature", "Time", as.character(ocr2_wu["Pointdodge"]),
               ymins, ymaxes)
    
    ## Save residual plots
    if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
      if(args$I == ".svg"){
        svglite(paste0(args$Output, "/Residual_", other_config_row$Graph, args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(args$Output, "/QQ_", other_config_row$Graph, args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, path = args$Output)
        ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, path = args$Output)
      }
    } else {
      if(args$I == ".svg"){
        svglite(paste0(other_stat_dir, "/Residual_", other_config_row$Graph, args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(other_stat_dir, "/QQ_", other_config_row$Graph, args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
        ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
      }
    }
    
    #######################################################
    # Custom  
  } else {
    if(ocr2["Resp"] %in% colnames(tbl0)) {
      
      # Set graphing variables as a vector.
      box_vars <- c(ocr2["Xvar"], ocr2["Pointdodge"], ocr2["Facet1"], ocr2["Facet2"])
      box_vars <- box_vars[box_vars != ""]
      if(length(box_vars) == 0){  stop("Custom optional graph requires an independent variable.") }
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
        tbl0 <- tbl0 %>%
          dplyr::filter(Breath_Inclusion_Filter == 1) 
      } 
      
      ## Data frame for plotting
      other_graph_df <- tbl0 %>%
        dplyr::group_by_at(c(box_vars, "MUID")) %>%
        dplyr::summarise_at(as.character(ocr2["Resp"]), mean, na.rm = TRUE) %>%
        dplyr::ungroup()
      
      # Check that variables are factors; set in order of appearance in data.
      for(jj in box_vars){
        other_graph_df[[jj]] <- factor(other_graph_df[[jj]], levels = unique(tbl0[[jj]]))
      }
      
      # Set order of categories in variables as specified by the user, if specified.
      regraph_vars <- box_vars[which(box_vars %in% graph_v)] 
      if(length(regraph_vars) != 0){
        other_graph_df <- graph_reorder(other_graph_df, regraph_vars, graph_vars, tbl0)
      }
      
      name_part <- str_replace_all(c(other_config_row$Variable, other_config_row$Graph), "[[:punct:]]", "")
      graph_file <- paste0(name_part[1], "_", name_part[2], args$I) %>% str_replace_all(" ", "")
      
      # Runs stat modeling 
      # Assumes that each individual observation is relevant (and not mouse-level statistic.)
      if(length(unique(tbl0$MUID)) == nrow(tbl0)){
        other_mod_res <- stat_run_other(as.character(ocr2["Resp"]), other_inter_vars, other_covars, tbl0, FALSE)
      } else {
        other_mod_res <- stat_run(as.character(ocr2["Resp"]), other_inter_vars, other_covars, tbl0, FALSE)
      }
      
      # Make graph + save
      graph_make(as.character(ocr2["Resp"]), as.character(ocr2["Xvar"]), as.character(ocr2["Pointdodge"]), 
                 as.character(ocr2["Facet1"]), as.character(ocr2["Facet2"]), other_graph_df, 
                 tbl0, other_mod_res$rel_comp, box_vars, graph_file, other = TRUE, inc_filter = inclusion_filter,
                 as.character(ocr2_wu["Resp"]), as.character(ocr2_wu["Xvar"]), as.character(ocr2_wu["Pointdodge"]),
                 ymins, ymaxes)
      
      ## Save residual plots
      if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
        if(args$I == ".svg"){
          svglite(paste0(args$Output, "/Residual_", other_config_row$Graph, args$I))
          print(other_mod_res$residplot)
          dev.off()
          svglite(paste0(args$Output, "/QQ_", other_config_row$Graph, args$I))
          print(other_mod_res$qqplot)
          dev.off()
        } else {
          ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, path = args$Output)
          ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, path = args$Output)
        }
      } else {
        if(args$I == ".svg"){
          svglite(paste0(other_stat_dir, "/Residual_", other_config_row$Graph, args$I))
          print(other_mod_res$residplot)
          dev.off()
          svglite(paste0(other_stat_dir, "/QQ_", other_config_row$Graph, args$I))
          print(other_mod_res$qqplot)
          dev.off()
        } else {
          ggsave(paste0("Residual_", other_config_row$Graph, args$I), plot = other_mod_res$residplot, 
                 path = paste0(args$Output, "/OptionalStatResults/"))
          ggsave(paste0("QQ_", other_config_row$Graph, args$I), plot = other_mod_res$qqplot, 
                 path = paste0(args$Output, "/OptionalStatResults/"))
        }
      }
      
    } else {
      ## If the response variable doesn't exist, skip.
      stop(paste0("Unable to make graph ", other_config_row$Graph, "; unexpected response variable."))
    }
  }
  
  if(exists("other_mod_res")){
    return(other_mod_res)
  }
}

# Iterate through each of the rows in the config file.
## Create the desired plot for each row
if(nrow(other_config) > 0){
  
  ## Saving modeling results for each dependent variable
  other_mod_res_list <- list()
  ## Saves Tukey test results
  other_tukey_res_list <- list()
  ## Saves basic statistics
  other_b_stat_list <- list()
  
  
  other_stat_dir  <- paste0(args$Output, "/OptionalStatResults/")
  if(!dir.exists(other_stat_dir)){
    dirtest <- try(dir.create(other_stat_dir, recursive = TRUE))
  } 
  
  # Run optional graphs
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
   
    # Check for 0 variance responses.
    optional_box_vars <- c(ifelse(is.null(other_config_row$Xvar), "", other_config_row$Xvar),
                           ifelse(is.null(other_config_row$Pointdodge), "", other_config_row$Pointdodge),
                           ifelse(is.null(other_config_row$Facet1), "", other_config_row$Facet1),
                           ifelse(is.null(other_config_row$Facet2), "", other_config_row$Facet2))
    optional_box_vars <- optional_box_vars[optional_box_vars != ""]
    optional_box_vars <- c(optional_box_vars, other_config_row$Independent)
    
    if(length(optional_box_vars) != 0){
      optional_box_vars <- sapply(optional_box_vars, wu_convert)
    }

    if(sd(tbl0[[other_config_row$Variable]]) < 10^-9){
      warning(paste0(other_config_row$Variable, " is a (near) 0 variance response variable; computationally infeasible model fitting."))
      next
    } else if (any((tbl0 %>% group_by_at(optional_box_vars) %>% 
                    summarize_at(other_config_row$Variable, list(sd)))[[other_config_row$Variable]] <= 10^-9)){
      warning(paste0("No variation in values of ", other_config_row$Variable, " for one or more interaction groups; are these all zero?"))
      next
    }
    
    # Try to run stats, make optional graphs/
    stat_res_optional <- try(optional_graph_maker(other_config_row, tbl0, var_names, graph_vars, other_stat_dir, dirtest,
                                                  xvar, pointdodge, facet1, facet2))
    # Save stat results.
    if(class(stat_res_optional) != "try-error" && !is.null(stat_res_optional)){
      other_mod_res_list[[other_config_row$Graph]] <- stat_res_optional$lmer
      other_tukey_res_list[[other_config_row$Graph]] <- stat_res_optional$rel_comp
      other_b_stat_list[[other_config_row$Graph]] <- stat_res_optional$b_stat
    }
    
    if((other_config_row$Variable == "Weight") && ((is.na(other_config_row$Transformation)) || (other_config_row$Transformation == ""))){
      other_config_row$Transformation <- var_names$Transformation[which(var_names$Column == "Weight")]
    }
    
    if((other_config_row$Variable == "Age") && ((is.na(other_config_row$Transformation)) || (other_config_row$Transformation == ""))){
      other_config_row$Transformation <- var_names$Transformation[which(var_names$Column == "Age")]
    }
    
    # Optional graph transformations
    if((is.null(other_config_row$Transformation)) || (is.na(other_config_row$Transformation)) || (other_config_row$Transformation == "")){
      other_config_row$Transformation <- var_names$Transformation[which(var_names$Alias == other_config_row$Variable)]
    }
    
    if((!is.null(other_config_row$Transformation)) && (!is.na(other_config_row$Transformation)) && (other_config_row$Transformation != "")){ 
      if(any(tbl0[[other_config_row$Variable]] < 0, na.rm=TRUE)){
        ## Most transformations require non-negative variables.
        print("Optional graph response variable has negative values, potential transformations will not work.")
        next
      }
      transforms_resp <- unlist(strsplit(other_config_row$Transformation, "@"))
      for(jj in 1:length(transforms_resp)){
        new_colname <- paste0(other_config_row$Variable, "_", transforms_resp[jj])
        if(transforms_resp[jj] == "log10"){
          if(any(tbl0[[other_config_row$Variable]] <= 0, na.rm=TRUE)){
            ## Most transformations require non-negative variables.
            print(paste0("Response variable ", other_config_row$Variable," has exact 0 values, log transformations will not work."))
            next
          }
          tbl0[[new_colname]] <- log10(tbl0[[other_config_row$Variable]])
        } else if(transforms_resp[jj] == "log"){
          if(any(tbl0[[other_config_row$Variable]] <= 0, na.rm=TRUE)){
            ## Most transformations require non-negative variables.
            print(paste0("Response variable ", other_config_row$Variable," has exact 0 values, log transformations will not work."))
            next
          }
          tbl0[[new_colname]] <- log(tbl0[[other_config_row$Variable]])
        } else if(transforms_resp[jj] == "sqrt"){
          tbl0[[new_colname]] <- sqrt(tbl0[[other_config_row$Variable]])
        } else if(transforms_resp[jj] == "sq"){
          tbl0[[new_colname]] <- (tbl0[[other_config_row$Variable]])^2
        } else {
          next
        }
        trans_config_row <- other_config_row
        trans_config_row$Variable <- new_colname
        trans_config_row$Graph <- paste0(other_config_row$Graph, "_", transforms_resp[jj])
        stat_res_optional <- try(optional_graph_maker(trans_config_row, tbl0, var_names, graph_vars, other_stat_dir, dirtest,
                                                      xvar, pointdodge, facet1, facet2))
      }
      
      # Save stat results.
      if(class(stat_res_optional) != "try-error" && !is.null(stat_res_optional)){
        trans_graphname <- paste0(other_config_row$Graph, "_", transforms_resp[jj])
        other_mod_res_list[[trans_graphname]] <- stat_res_optional$lmer
        other_tukey_res_list[[trans_graphname]] <- stat_res_optional$rel_comp
        other_b_stat_list[[trans_graphname]] <- stat_res_optional$b_stat
      }
    }
    
  }
 
  # Save stat results tables in Excel
  mod_res_list_save <- other_mod_res_list
  names(mod_res_list_save) <- str_trunc(names(mod_res_list_save), 31, side = "center", ellipsis = "___")
  tukey_res_list_save <- other_tukey_res_list
  names(tukey_res_list_save) <- str_trunc(names(tukey_res_list_save), 31, side = "center", ellipsis = "___")
  b_stat_list_save <- other_b_stat_list
  names(b_stat_list_save) <- str_trunc(names(b_stat_list_save), 31, side = "center", ellipsis = "___")
  
  # Save statistics results to Excel.
  if(length(mod_res_list_save) > 0){
    if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
      try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/optional_stat_res.xlsx"), rowNames=TRUE))
      try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/optional_tukey_res.xlsx"), rowNames=TRUE))
      try(openxlsx::write.xlsx(b_stat_list_save, file=paste0(args$Output, "/optional_stat_basic.xlsx"), rowNames=TRUE))
    } else {
      try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/OptionalStatResults/stat_res.xlsx"), rowNames=TRUE))
      try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/OptionalStatResults/tukey_res.xlsx"), rowNames=TRUE))
      try(openxlsx::write.xlsx(b_stat_list_save, file=paste0(args$Output, "/OptionalStatResults/stat_basic.xlsx"), rowNames=TRUE))
    }
  }
  # Memory clearing
  rm(mod_res_list_save)
  rm(tukey_res_list_save)
  rm(b_stat_list_save)
}



#######################################
##### Apneas & Sighs ##################
#######################################

# Functionality to make graphs for sigh and apnea rates.
if(sighs || apneas){
  print("Making apnea and sigh graphs")
  
  # Set graphing variables as a vector.
  box_vars <- c(xvar, pointdodge, facet1, facet2)
  box_vars <- box_vars[box_vars != ""]
  
  # Summarize data by mouse for plotting.
  ## Find total measurement time for each interaction group + mouse.
  timetab <- tbl0 %>%
    dplyr::group_by_at(c(box_vars, "MUID")) %>%
    dplyr::summarise_at(var_names$Alias[which(var_names$Column == "Breath_Cycle_Duration")], sum, na.rm = TRUE)
  colnames(timetab)[ncol(timetab)] <- "measuretime"  
  ## Find number of sighs/apneas for each interaction group + mouse.
  eventtab <- tbl0 %>%
    dplyr::group_by_at(c(box_vars, "MUID")) %>%
    dplyr::summarise(sighs = sum(Sigh), apneas = sum(Apnea))
  ## Join tables to calculate rates.
  eventtab_join <- inner_join(eventtab, timetab, by = c(box_vars, "MUID")) %>%
    mutate(SighRate = sighs/measuretime*60, ApneaRate = apneas/measuretime*60)
  
  # Set label + internal variable names.
  ## Depending on if sighs and/or apneas are desired.
  r_vars <- c()
  r_vars_wu <- c()
  if(sighs){
    r_vars <- c(r_vars, "SighRate")
    r_vars_wu <- c(r_vars_wu, "Sigh Rate (1/min)")
    
    # Transforms for sigh rate.
    sigh_transform <- other_config$Transformation[which(other_config$Graph == "Sighs")]
    if((is.null(sigh_transform)) || (is.na(sigh_transform)) || (sigh_transform == "")){ 
      sigh_transform <- var_names$Transformation[which(var_names$Alias == "Sigh")] 
    }
    if((!is.null(sigh_transform)) && (!is.na(sigh_transform)) && (sigh_transform != "")){
      transforms_resp <- unlist(strsplit(sigh_transform, "@"))
      for(jj in 1:length(transforms_resp)){
        new_colname <- paste0("SighRate", "_", transforms_resp[jj])
        new_graphname <- paste0("Sigh Rate (1/min), ", transforms_resp[jj])
        if(transforms_resp[jj] == "log10"){
          if(any(eventtab_join[["SighRate"]] <= 0, na.rm=TRUE)){
            ## Most transformations require non-negative variables.
            print("Sigh rate has exact 0 values, log10 transform will not work.")
            next
          }
          eventtab_join[[new_colname]] <- log10(eventtab_join[["SighRate"]])
        } else if(transforms_resp[jj] == "log"){
          if(any(eventtab_join[["SighRate"]] <= 0, na.rm=TRUE)){
            ## Most transformations require non-negative variables.
            print("Sigh rate has exact 0 values, log transform will not work.")
            next
          }
          eventtab_join[[new_colname]] <- log(eventtab_join[["SighRate"]])
        } else if(transforms_resp[jj] == "sqrt"){
          eventtab_join[[new_colname]] <- sqrt(eventtab_join[["SighRate"]])
        } else if(transforms_resp[jj] == "sq"){
          eventtab_join[[new_colname]] <- (eventtab_join[["SighRate"]])^2
        } else {
          next
        }
        r_vars <- c(r_vars, new_colname)
        r_vars_wu <- c(r_vars_wu, new_graphname)
      }
    }
  }
  
  if(apneas){
    r_vars <- c(r_vars, "ApneaRate")
    r_vars_wu <- c(r_vars_wu, "Apnea Rate (1/min)")
    apnea_transform <- other_config$Transformation[which(other_config$Graph == "Apneas")] 
    if((is.null(apnea_transform)) || (is.na(apnea_transform)) || (apnea_transform == "")){ 
      apnea_transform <- var_names$Transformation[which(var_names$Alias == "Apnea")]
    }
    # Transforms for apnea rate.
    if((!is.null(apnea_transform)) && (!is.na(apnea_transform)) && (apnea_transform != "")){
      transforms_resp <- unlist(strsplit(apnea_transform, "@"))
      for(jj in 1:length(transforms_resp)){
        new_colname <- paste0("ApneaRate", "_", transforms_resp[jj])
        new_graphname <- paste0("Apnea Rate (1/min), ", transforms_resp[jj])
        if(transforms_resp[jj] == "log10"){
          if(any(eventtab_join[["ApneaRate"]] <= 0, na.rm=TRUE)){
            ## Most transformations require non-negative variables.
            print("Sigh rate has exact 0 values, log10 transform will not work.")
            next
          }
          eventtab_join[[new_colname]] <- log10(eventtab_join[["ApneaRate"]])
        } else if(transforms_resp[jj] == "log"){
          if(any(eventtab_join[["ApneaRate"]] <= 0, na.rm=TRUE)){
            ## Most transformations require non-negative variables.
            print("Sigh rate has exact 0 values, log transform will not work.")
            next
          }
          eventtab_join[[new_colname]] <- log(eventtab_join[["ApneaRate"]])
        } else if(transforms_resp[jj] == "sqrt"){
          eventtab_join[[new_colname]] <- sqrt(eventtab_join[["ApneaRate"]])
        } else if(transforms_resp[jj] == "sq"){
          eventtab_join[[new_colname]] <- (eventtab_join[["ApneaRate"]])^2
        } else {
          next
        }
        r_vars <- c(r_vars, new_colname)
        r_vars_wu <- c(r_vars_wu, new_graphname)
      }
    }
  }
  
  ## Saving modeling results for each dependent variable
  sa_mod_res_list <- list()
  ## Saves Tukey test results
  sa_tukey_res_list <- list()
  
  other_stat_dir  <- paste0(args$Output, "/OptionalStatResults/")
  if(!dir.exists(other_stat_dir)){
    dirtest <- try(dir.create(other_stat_dir, recursive = TRUE))
  } 
  
  # Loop to make sighs + apneas graphs.
  for(ii in 1:length(r_vars)){
    
    if(sd(eventtab_join[[r_vars[ii]]]) < 10^-9) {
      warning(paste0("No variation in values of ", r_vars[ii], "; are these all zero?"))
      next
    } else if (any((eventtab_join %>% group_by_at(box_vars) %>% summarize_at(r_vars[ii], list(sd)))[[r_vars[ii]]] <= 10^-9)){
      warning(paste0("No variation in values of ", r_vars[ii], " for one or more interaction groups; are these all zero?"))
      next
    }
    
    eventtab_join %>% group_by_at(box_vars) %>% summarize_at(r_vars[ii], list(sd))
    
    graph_file <- paste0(r_vars[ii], args$I) %>% str_replace_all(" ", "")
    
    # Stat modeling, calculated ONLY using graphing variables as independent variables.
    if(length(unique(eventtab_join$MUID)) == nrow(eventtab_join)){
      other_mod_res <- stat_run_other(r_vars[ii], box_vars, character(0), eventtab_join, FALSE)
    } else {
      other_mod_res <- stat_run(r_vars[ii], box_vars, character(0), eventtab_join, FALSE)
    }
    
    # Save stat results.
    sa_mod_res_list[[r_vars[ii]]] <- other_mod_res$lmer
    sa_tukey_res_list[[r_vars[ii]]] <- other_mod_res $rel_comp
    
    # Set order of categories in variables as specified by the user, if specified.
    eventtab_join_graph <- graph_reorder(eventtab_join, box_vars, graph_vars, tbl0)
    
    # Make graph + save
    sa_test <- try(graph_make(r_vars[ii], xvar, pointdodge, facet1, facet2, eventtab_join_graph, 
                              eventtab_join, other_mod_res$rel_comp, box_vars, graph_file, other = TRUE,  
                              inc_filter = FALSE, r_vars_wu[ii], xvar_wu, pointdodge_wu))
    
    if(class(sa_test) == "try-error"){
      print(paste0('Failed to make plots for ', r_vars[ii]))
      next
    }
    
    ## Save residual plots
    if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
      if(args$I == ".svg"){
        svglite(paste0(args$Output, "/Residual_", r_vars[ii], args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(args$Output, "/QQ_", r_vars[ii], args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", r_vars[ii], args$I), plot = other_mod_res$residplot, path = args$Output)
        ggsave(paste0("QQ_", r_vars[ii], args$I), plot = other_mod_res$qqplot, path = args$Output)
      }
    } else {
      if(args$I == ".svg"){
        svglite(paste0(other_stat_dir, "/Residual_", r_vars[ii], args$I))
        print(other_mod_res$residplot)
        dev.off()
        svglite(paste0(other_stat_dir, "/QQ_", r_vars[ii], args$I))
        print(other_mod_res$qqplot)
        dev.off()
      } else {
        ggsave(paste0("Residual_", r_vars[ii], args$I), plot = other_mod_res$residplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
        ggsave(paste0("QQ_", r_vars[ii], args$I), plot = other_mod_res$qqplot, 
               path = paste0(args$Output, "/OptionalStatResults/"))
      }
    }
  }
  
  # Save stat results tables in Excel
  mod_res_list_save <- sa_mod_res_list
  names(mod_res_list_save) <- str_trunc(names(mod_res_list_save), 31, side = "center", ellipsis = "___")
  tukey_res_list_save <- sa_tukey_res_list
  names(tukey_res_list_save) <- str_trunc(names(tukey_res_list_save), 31, side = "center", ellipsis = "___")
  
  # Save statistics results to Excel.
  if(length(mod_res_list_save) > 0){
    if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
      try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/sighapnea_stat_res.xlsx"), rowNames=TRUE))
      try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/sighapnea_tukey_res.xlsx"), rowNames=TRUE))
    } else {
      try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/OptionalStatResults/sighapnea_stat_res.xlsx"), rowNames=TRUE))
      try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/OptionalStatResults/sighapnea_tukey_res.xlsx"), rowNames=TRUE))
    }
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
  
  poincare_v <- c(xvar, pointdodge, facet1, facet2)
  poincare_v <- poincare_v[poincare_v != ""]
  
  # Settings for graphing variables
  ## Point color
  if(pointdodge != ""){
    poincare_df[[pointdodge]] <- factor(graph_data[[pointdodge]][-nrow(graph_data)], 
                             levels = unique(graph_data[[pointdodge]]))
    pointdodge_g <- pointdodge
  } else {
    pointdodge_g <- NULL
  }
  
  ## Row panels.
  if(facet1 != ""){
    poincare_df[[facet1]] <- factor(graph_data[[facet1]][-nrow(graph_data)], 
                                 levels = unique(graph_data[[facet1]]))
    facet1_g <- facet1
  } else {
    facet1_g <- "."
  }
  
  ## Column panels.
  if(facet2 != ""){
    poincare_df[[facet2]] <- factor(graph_data[[facet2]][-nrow(graph_data)], 
                                 levels = unique(graph_data[[facet2]]))
    facet2_g <- facet2
  } else {
    facet2_g <- "."
  }
  
  ## Different files
  if(xvar != ""){
    if(is.numeric(graph_data[[xvar]])){
      print(paste0("Invalid Xvar for poincare plot ", xvar))
      next
    }
    
    poincare_df[[xvar]] <- factor(graph_data[[xvar]][-nrow(graph_data)], 
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
    for(ll in unique(poincare_df[[xvar]])) {
      poincare_df_sub <- poincare_df[which(poincare_df[[xvar]] == ll),]

      # Set order of categories in variables as specified by the user, if specified.
      poincare_df_sub <- graph_reorder(poincare_df_sub, poincare_v, 
                                       graph_vars, poincare_df_sub)
      # Make graph + save
      p <- ggplot() +
        geom_point(aes_string(x = "lag", y = "lead", color = pointdodge_g), data = poincare_df_sub) +
        geom_abline(slope = 1, intercept = 0) +
        facet_grid(form_string) + 
        scale_color_manual(values = cPalette) +
        labs(x = "T", y = "T+1", color = pointdodge_wu, title = paste0("Poincare: ", resp_var, " ~ ", ll)) +
        theme_few(base_size = 7) 
      
      name_part <- str_replace_all(c(resp_var, ll), "[[:punct:]]", "")
      graph_file <- str_replace_all(paste0("Poincare_", name_part[1], "_", name_part[2], args$I), " ", "") %>% str_replace_all(" ", "")
      
      if(grepl(".svg", graph_file)){
        svglite(paste0(args$Output, "/", graph_file), width = 7, height = 7)
        print(p)
        dev.off()
      } else {
        ggsave(graph_file, plot = p, path = args$Output, width = 17.5, height = 17.5, units = "cm", dpi = 300)
      }
      
    }
    
  } else {
    
    # Set order of categories in variables as specified by the user, if specified.
    poincare_df <- graph_reorder(poincare_df, poincare_v, 
                                     graph_vars, poincare_df)
    
    # Make graph + save
    p <- ggplot() +
      geom_point(aes_string(x = "lag", y = "lead", color = pointdodge_g), data = poincare_df) +
      geom_abline(slope = 1, intercept = 0) +
      facet_grid(form_string) + 
      scale_color_manual(values = cPalette) +
      labs(x = "T", y = "T+1", color = pointdodge_wu, title = paste0("Poincare: ", resp_var)) +
      theme_few(base_size = 7) 
    
    name_part <- str_replace_all(resp_var, "[[:punct:]]", "")
    graph_file <- str_replace_all(paste0("Poincare_", name_part, args$I), " ", "") %>% str_replace_all(" ", "")
    
    if(grepl(".svg", graph_file)){
      svglite(paste0(args$Output, "/", graph_file), width = 7, height = 7)
      print(p)
      dev.off()
    } else {
      ggsave(graph_file, plot = p, path = args$Output, width = 17.5, height = 17.5, units = "cm", dpi = 300)
    }
    
  }
  return()
}



# Run poincare graph function
if((!is.na(poincare_vars)) && (length(poincare_vars) != 0)){
  # Check for desired transformations for extra poincare plots.
  raw_pc_vars <- poincare_vars
  pc_transform_set <- var_names$Transformation[which(var_names$Poincare != 0)]
  for(pp in 1:length(pc_transform_set)){
    if((!is.na(pc_transform_set[pp])) && (pc_transform_set[pp] != "")){
      transforms_resp <- unlist(strsplit(pc_transform_set[pp], "@"))
      if(any(tbl0[[raw_pc_vars[pp]]] < 0, na.rm=TRUE)){
        ## Most transformations require non-negative variables.
        print(paste0("Response variable ", raw_pc_vars[pp]," has negative values, potential transformations will not work."))
      } else {
        ## Create transformed variables.
        for(jj in 1:length(transforms_resp)){
          new_colname <- paste0(raw_pc_vars[pp], "_", transforms_resp[jj])
          if(!(new_colname %in% names(tbl0))){
            if(transforms_resp[jj] == "log10"){
              if(any(tbl0[[response_vars[ii]]] <= 0, na.rm=TRUE)){
                ## Most transformations require non-negative variables.
                print(paste0("Response variable ", raw_pc_vars[pp]," has exact 0 values, log transformations will not work."))
                next
              }
              tbl0[[new_colname]] <- log10(tbl0[[raw_pc_vars[pp]]])
            } else if(transforms_resp[jj] == "log"){
              if(any(tbl0[[response_vars[ii]]] <= 0, na.rm=TRUE)){
                ## Most transformations require non-negative variables.
                print(paste0("Response variable ", raw_pc_vars[pp]," has exact 0 values, log transformations will not work."))
                next
              }
              tbl0[[new_colname]] <- log(tbl0[[raw_pc_vars[pp]]])
            } else if(transforms_resp[jj] == "sqrt"){
              tbl0[[new_colname]] <- sqrt(tbl0[[raw_pc_vars[pp]]])
            } else if(transforms_resp[jj] == "sq"){
              tbl0[[new_colname]] <- (tbl0[[raw_pc_vars[pp]]])^2
            } else {
              next
            }
            poincare_vars <- c(poincare_vars, new_colname)
          }
        }
      }
    }
  }
  for(ii in 1:length(poincare_vars)){
    print((paste0("Making Poincare plot ", ii, "/", length(poincare_vars))))
    try(poincare_graph(poincare_vars[ii], tbl0, xvar, pointdodge, facet1,
                   facet2, pointdodge_wu))
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
html_try <- try(rmarkdown::render(rmd_file, output_dir = args$Output, 
                                  output_format = "html_document"))

# If there is an error, 
if(class(html_try) == "try-error"){
  print("No Summary Rmd file or pandocs found.")
}
