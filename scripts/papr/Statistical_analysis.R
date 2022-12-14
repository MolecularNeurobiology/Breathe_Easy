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
##### DESCRIPTION #######
#########################
# stat_runner.r runs LMER tests on all variables assigned in the subGUI by the user. 
# This code performs necessary adjustments/ changes required for stats to run properly and filters the results.
print("Running Statistics")

#########################
######### LMER ##########
#########################
# Helper function for avoiding parsing errors from strings with leading numbers.
## Inputs:
### string_val: name of category
## Outputs:
### New category name, with parentheses removed.
X_num <- function(string_val) {
  if(grepl("[0-9]", substr(string_val, 1, 1))){
    return(paste0("X", string_val))
  } else {
    return(string_val)
  }
}

# Runs the statistical modeling step
## Inputs:
### resp_var: character string, name of dependent variable.
### inter_vars: character vector, names of independent variables.
### cov_vars: character vector, names of covariates.
### run_data: data frame, data to fit model on
### inc_filter: boolean, whether breath inclusion filter should be used.
## Outputs (saved in list):
### rel_comp: data frame, pairwise comparison results for biologically relevant comparisons
### lmer: data frame, coefficient estimates from the model for each of the interaction groups
### residplot: ggplot object, the residual plot from the model.
### qqplot: ggplot object, the q-q plot for the model residuals.
stat_run <- function(resp_var, inter_vars, cov_vars, run_data, inc_filt = TRUE){
  
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
  # Needs to be processed in the same manner in the graph_maker function as well.
  for(vv in inter_vars){
      run_data[[vv]] <- run_data[[vv]] %>% as.character() %>% str_replace_all("[[:punct:]]", "") %>% str_replace_all(" ", "")
      run_data[[vv]] <- sapply(run_data[[vv]], X_num) %>% unname()
  }
  
  # Create list for function output.
  return_values <- list()
  # Create interaction variable string
  interact_string <- paste0("run_data$interact <- with(run_data, interaction(", paste(inter_vars, collapse = ", "), "))")
  eval(parse(text = interact_string))
  # Create covariates variable string
  covar_formula_string <- paste(c(0, cov_vars), collapse = "+")
  # Create full formula string for modeling.
  form <- as.formula(paste0(resp_var, " ~ (1|MUID) + interact + ", covar_formula_string))
  
  # Run model
  temp_mod <- lmer(form, data = run_data)
  
  # Create all relevant comparisons for pairwise comparison testing.
  ## Find all interaction groups in model.
  all_names <- grep("interact", names(fixef(temp_mod)), value = TRUE) %>% str_replace_all("interact", "")
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
  comp_list <- comb_list[which(row_mismatches == 1)]
  
  ## Make names of biologically relevant comparisons for glht function
  for(qq in 1:length(comp_list)){
    comp_list[qq] <- paste0(comp_list[qq], " = 0")
  }
  ## Run pairwise comparison tests, with multiple testing correction.
  temp_tukey <- glht(temp_mod , linfct = mcp(interact = comp_list))
  
  ## Create output table
  ### Contains coefficient estimate, standard error, t-statistic, and p-value.
  vt <- summary(temp_tukey)$test
  mytest <- cbind(vt$coefficients, vt$sigma, vt$tstat, vt$pvalues)
  error <- attr(vt$pvalues, "error") 
  pname <- switch(temp_tukey$alternativ,
                  less=paste("Pr(<", ifelse(temp_tukey$df == 0, "z", "t"), ")", sep = ""),
                  greater=paste("Pr(>", ifelse(temp_tukey$df == 0, "z", "t"), ")", sep = ""),
                  two.sided=paste("Pr(>|", ifelse(temp_tukey$df == 0, "z", "t"), "|)", sep = ""))
  colnames(mytest) <- c("Estimate", "Std. Error", ifelse(temp_tukey$df == 0, "z value", "t value"), pname)
  vttukey <- as.data.frame(xtable::xtable(mytest))
  colnames(vttukey) <- c("Estimate", "StdError", "tvalue", "pvalue")
  
  # Make residual plots
  ## Raw residual plot
  g1 <- ggplot() +
    geom_point(aes(x = fitted(temp_mod), y = resid(temp_mod))) +
    labs(x = "Fitted", y = "Residual", title = paste0("Residuals: ", resp_var, " ~ ", paste(inter_vars, collapse = " + "))) + 
    geom_abline(slope = 0, intercept = 0) +
    theme_few() 
  
  ## Q-Q plot
  g2 <- ggplot() +
    geom_qq(aes(sample = resid(temp_mod))) +
    labs(x = "Empirical Quantile", y = "Theoretical Quantile", title = paste0("Q-Q: ", resp_var, " ~ ", paste(inter_vars, collapse = " + "))) + 
    geom_qq_line(aes(sample = resid(temp_mod))) +
    theme_few() 
    
    
  # Create return values
  return_values$rel_comp <- vttukey
  return_values$lmer <- summary(temp_mod)$coef
  return_values$residplot <- g1
  return_values$qqplot <- g2
  return_values$b_stat <- b_stat_data
  
  return(return_values)
}

# Create directory to save stat results
stat_dir  <- paste0(args$Output, "/StatResults/")
if(!dir.exists(stat_dir)){
  dirtest <- try(dir.create(paste0(args$Output, "/StatResults/"), recursive = TRUE))
} 

#Runs LMER for all selected variables above and provides printed stamps for user to monitor progress.
## Saves modeling results for each dependent variable
mod_res_list <- list()
## Saves Tukey test results
tukey_res_list <- list()
## Saves basic statistics
b_stat_list <- list()

if((!is.na(response_vars)) && (!is_empty(response_vars)) && (!is.na(interaction_vars)) && (!is_empty(interaction_vars))){ 
  # For each response variable, run on original variable, then on all desired transformations.
  for(ii in 1:length(response_vars)){
    
    print(paste0("Running model for ", response_vars[ii]))
    
    # NA check
    if(sum(!is.na(tbl0[[response_vars[ii]]]) & tbl0$Breath_Inclusion_Filter) <= 1){
      warning(paste0(response_vars[ii], " does not have enough non-NA values."))
      next
    }
    
    # 0 variance check
    if(sd(tbl0[[response_vars[ii]]], na.rm = TRUE) < 10^-9){
      warning(paste0(response_vars[ii], " is a (near) 0 variance response variable; computationally infeasible model fitting."))
      next
    } else if (any((tbl0 %>% group_by_at(interaction_vars) %>% 
                    summarize_at(response_vars[ii], sd, na.rm = TRUE))[[response_vars[ii]]] <= 10^-9)){
      warning(paste0("No variation in values of ", response_vars[ii], " for one or more interaction groups; are these all zero?"))
      next
    }
    
    # Runs the model on the original, non-transformed dependent variable (if selected by user)
    if(((is.na(transform_set[ii])) || (transform_set[ii] == "") || (grepl("non", transform_set[ii])))){
      
      ## Run models
      mod_res <- try(stat_run(response_vars[ii], interaction_vars, covariates, tbl0, inc_filt = TRUE))
      
      ## Save parts of output
      if(class(mod_res) != "try-error" && !is.null(mod_res)){
        mod_res_list[[response_vars[ii]]] <- mod_res$lmer
        tukey_res_list[[response_vars[ii]]] <- mod_res$rel_comp
        b_stat_list[[response_vars[ii]]] <- mod_res$b_stat
        
        ## Save residual plots
        if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
          if(args$I == ".svg"){
            svglite(paste0(args$Output, "/Residual_", response_vars[ii], args$I))
            print(mod_res$residplot)
            dev.off()
            svglite(paste0(args$Output, "/QQ_", response_vars[ii], args$I))
            print(mod_res$qqplot)
            dev.off()
          } else {
            ggsave(paste0("Residual_", response_vars[ii], args$I), plot = mod_res$residplot, path = args$Output)
            ggsave(paste0("QQ_", response_vars[ii], args$I), plot = mod_res$qqplot, path = args$Output)
          }
        } else {
          if(args$I == ".svg"){
            svglite(paste0(stat_dir, "/Residual_", response_vars[ii], args$I))
            print(mod_res$residplot)
            dev.off()
            svglite(paste0(stat_dir, "/QQ_", response_vars[ii], args$I))
            print(mod_res$qqplot)
            dev.off()
          } else {
            ggsave(paste0("Residual_", response_vars[ii], args$I), plot = mod_res$residplot, path = stat_dir)
            ggsave(paste0("QQ_", response_vars[ii], args$I), plot = mod_res$qqplot, path = stat_dir)
          }
        }
      }
    }
    
    # Runs stat models for desired transformations (if selected by user)
    if((!is.na(transform_set[ii])) && (transform_set[ii] != "")){
      ## Assumes desired transformation are concatenated as a character string, with separator character '@'.
      transforms_resp <- unlist(strsplit(transform_set[ii], "@"))
      if(any(tbl0[[response_vars[ii]]] < 0, na.rm=TRUE)){
        ## Most transformations require non-negative variables.
        print(paste0("Response variable ", response_vars[ii]," has negative values, potential transformations will not work."))
        transform_set[ii] <- NA
      } else {
        ## Create transformed variables.
        for(jj in 1:length(transforms_resp)){
          new_colname <- paste0(response_vars[ii], "_", transforms_resp[jj])
          print(paste0("Running model for ", new_colname))
          
          if(transforms_resp[jj] == "log10"){
            if(any(tbl0[[response_vars[ii]]] <= 0, na.rm=TRUE)){
              ## Most transformations require non-negative variables.
              print(paste0("Response variable ", response_vars[ii]," has exact 0 values, log transformations will not work."))
              next
            }
            tbl0[[new_colname]] <- log10(tbl0[[response_vars[ii]]])
          } else if(transforms_resp[jj] == "log"){
            if(any(tbl0[[response_vars[ii]]] <= 0, na.rm=TRUE)){
              ## Most transformations require non-negative variables.
              print(paste0("Response variable ", response_vars[ii]," has exact 0 values, log transformations will not work."))
              next
            }
            tbl0[[new_colname]] <- log(tbl0[[response_vars[ii]]])
          } else if(transforms_resp[jj] == "sqrt"){
            tbl0[[new_colname]] <- sqrt(tbl0[[response_vars[ii]]])
          } else if(transforms_resp[jj] == "sq"){
            tbl0[[new_colname]] <- (tbl0[[response_vars[ii]]])^2
          } else {
            next
          }
          
          if(sd(tbl0[[new_colname]], na.rm = TRUE) < 10^-9){
            warning(paste0(new_colname, " is a (near) 0 variance response variable; computationally infeasible model fitting."))
            next
          } else if (any((tbl0 %>% group_by_at(interaction_vars) %>% 
                          summarize_at(new_colname, sd, na.rm = TRUE))[[new_colname]] <= 10^-9)){
            warning(paste0("No variation in values of ", new_colname, " for one or more interaction groups; are these all zero?"))
            next
          }
          
          
          ## Run models
          mod_res <- try(stat_run(new_colname, interaction_vars, covariates, tbl0, inc_filt = TRUE))
          
          ## Save parts of output
          if(class(mod_res) != "try-error" && !is.null(mod_res)){
            mod_res_list[[new_colname]] <- mod_res$lmer
            tukey_res_list[[new_colname]] <- mod_res$rel_comp
            b_stat_list[[new_colname]] <- mod_res$b_stat
            
            ## Save residual plots
            if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
              if(args$I == ".svg"){
                svglite(paste0(args$Output, "/Residual_", new_colname, args$I))
                print(mod_res$residplot)
                dev.off()
                svglite(paste0(args$Output, "/QQ_", new_colname, args$I))
                print(mod_res$qqplot)
                dev.off()
              } else {
                ggsave(paste0("Residual_", new_colname, args$I), plot = mod_res$residplot, path = args$Output)
                ggsave(paste0("QQ_", new_colname, args$I), plot = mod_res$qqplot, path = args$Output)
              }
            } else {
              if(args$I == ".svg"){
                svglite(paste0(stat_dir, "/Residual_", new_colname, args$I))
                print(mod_res$residplot)
                dev.off()
                svglite(paste0(stat_dir, "/QQ_", new_colname, args$I))
                print(mod_res$qqplot)
                dev.off()
              } else {
                ggsave(paste0("Residual_", new_colname, args$I), plot = mod_res$residplot, path = stat_dir)
                ggsave(paste0("QQ_", new_colname, args$I), plot = mod_res$qqplot, path = stat_dir)
              }
            }
          }
        }
      }
    }
  }
  
  # Save stat results tables in Excel
  mod_res_list_save <- mod_res_list
  names(mod_res_list_save) <- str_trunc(names(mod_res_list_save), 31, side = "center", ellipsis = "___")
  tukey_res_list_save <- tukey_res_list
  names(tukey_res_list_save) <- str_trunc(names(tukey_res_list_save), 31, side = "center", ellipsis = "___")
  b_stat_list_save <- b_stat_list
  names(b_stat_list_save) <- str_trunc(names(b_stat_list_save), 31, side = "center", ellipsis = "___")

  # Save basic statistics results to Excel.
  if(exists("dirtest") && ((class(dirtest) == "try-error") || !dirtest)){
    try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/stat_res.xlsx"), rowNames=TRUE))
    try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/tukey_res.xlsx"), rowNames=TRUE))
    try(openxlsx::write.xlsx(b_stat_list_save, file=paste0(args$Output, "/stat_basic.xlsx"), rowNames=TRUE))
  } else {
    try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/StatResults/stat_res.xlsx"), rowNames=TRUE))
    try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/StatResults/tukey_res.xlsx"), rowNames=TRUE))
    try(openxlsx::write.xlsx(b_stat_list_save, file=paste0(args$Output, "/StatResults/stat_basic.xlsx"), rowNames=TRUE))
  }
  # Memory clearing
  rm(mod_res_list_save)
  rm(tukey_res_list_save)
  rm(b_stat_list_save)
}

# Savepoint
save_atp <- try(save.image(file=paste0(args$Output, "/myEnv_",format(Sys.time(),'%Y%m%d_%H%M%S'),".RData")))
if(class(save_atp) == "try-error") {save.image(file=paste0("./myEnv_", format(Sys.time(),'%Y%m%d_%H%M%S'),".RData"))}