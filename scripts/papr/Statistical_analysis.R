# DESCRIPTION:
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
stat_run <- function(resp_var, inter_vars, cov_vars, run_data, inc_filt = FALSE){
  
  # Removes rows with NAs and breath inclusion filter.
  if(inc_filt){
    run_data <- run_data %>% drop_na(any_of(inter_vars)) %>% dplyr::filter(Breath_Inclusion_Filter == 1)
  } else {
    run_data <- run_data %>% drop_na(any_of(inter_vars))
  }
  
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
  covar_formula_string <- paste(c(1, cov_vars), collapse = "+")
  # Create full formula string for modeling.
  form <- as.formula(paste0(resp_var, " ~ (1|MUID) + interact + ", covar_formula_string))
  
  # Run model
  temp_mod <- lmer(form, data = run_data)
  
  # Create all relevant comparisons for pairwise comparison testing.
  ## Find all interaction groups in model.
  all_names <- grep("interact", names(fixef(temp_mod)), value = TRUE) %>% str_replace_all("interact", "")
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
    labs(x = "Fitted", y = "Residual") + 
    geom_abline(slope = 0, intercept = 0) +
    theme_few() 
  
  ## Q-Q plot
  g2 <- ggplot() +
    geom_qq(aes(sample = resid(temp_mod))) +
    labs(x = "Empirical Quantile", y = "Theoretical Quantile") + 
    geom_qq_line(aes(sample = resid(temp_mod))) +
    theme_few() 
  
  # Create return values
  return_values$rel_comp <- vttukey
  return_values$lmer <- summary(temp_mod)$coef
  return_values$residplot <- g1
  return_values$qqplot <- g2
  
  return(return_values)
}

# Create directory to save stat results
stat_dir  <- paste0(args$Output, "/StatResults/")
if(!dir.exists(stat_dir)){
  dirtest <- try(dir.create(paste0(args$Output, "/StatResults/")))
} 

#Runs LMER for all selected variables above and provides printed stamps for user to monitor progress.
## Saves modeling results for each dependent variable
mod_res_list <- list()
## Saves Tukey test results
tukey_res_list <- list()

if((!is.na(response_vars)) && (!is_empty(response_vars)) && (!is.na(interaction_vars)) && (!is_empty(interaction_vars))){ 
  # For each response variable, run on original variable, then on all desired transformations.
  for(ii in 1:length(response_vars)){
    
    # Runs the model on the original, non-transformed dependent variable (if selected by user)
    if(((is.na(transform_set[ii])) || (transform_set[ii] == "") || (grepl("non", transform_set[ii])))){
      print(paste0("Running model for ", response_vars[ii]))
      ## Run models
      mod_res <- stat_run(response_vars[ii], interaction_vars, covariates, tbl0, inc_filt = TRUE)
      mod_res_list[[response_vars[ii]]] <- mod_res$lmer
      tukey_res_list[[response_vars[ii]]] <- mod_res$rel_comp
      ## Save residual plots
      if(exists("dirtest") && (class(dirtest) == "try-error")){
        ggsave(paste0("Residual_", response_vars[ii], args$I), plot = mod_res$residplot, path = args$Output)
        ggsave(paste0("QQ_", response_vars[ii], args$I), plot = mod_res$qqplot, path = args$Output)
      } else {
        ggsave(paste0("Residual_", response_vars[ii], args$I), plot = mod_res$residplot, path = paste0(args$Output, "/StatResults/"))
        ggsave(paste0("QQ_", response_vars[ii], args$I), plot = mod_res$qqplot, path = paste0(args$Output, "/StatResults/"))
      }
    }
    
    # Runs stat models for desired transformations (if selected by user)
    if((!is.na(transform_set[ii])) && (transform_set[ii] != "")){
      ## Assumes desired transformation are concatenated as a character string, with separator character '@'.
      transforms_resp <- unlist(strsplit(transform_set[ii], "@"))
      if(any(tbl0[[response_vars[ii]]] <= 0, na.rm=TRUE)){
        ## Most transformations require non-negative variables.
        print("Response variable has negative values, potential transformations will not work.")
      } else {
        ## Create transformed variables.
        for(jj in 1:length(transforms_resp)){
          new_colname <- paste0(response_vars[ii], "_", transforms_resp[jj])
          if(transforms_resp[jj] == "log10"){
            tbl0[[new_colname]] <- log10(tbl0[[response_vars[ii]]])
          } else if(transforms_resp[jj] == "log"){
            tbl0[[new_colname]] <- log(tbl0[[response_vars[ii]]])
          } else if(transforms_resp[jj] == "sqrt"){
            tbl0[[new_colname]] <- sqrt(tbl0[[response_vars[ii]]])
          } else if(transforms_resp[jj] == "sq"){
            tbl0[[new_colname]] <- (tbl0[[response_vars[ii]]])^2
          } else {
            next
          }
          
          print(paste0("Running model for ", new_colname))
          ## Run models
          mod_res <- stat_run(new_colname, interaction_vars, covariates, tbl0, inc_filt = TRUE)
          mod_res_list[[new_colname]] <- mod_res$lmer
          tukey_res_list[[new_colname]] <- mod_res$rel_comp
          ## Save residual plots
          if(exists("dirtest") && (class(dirtest) == "try-error")){
            ggsave(paste0("Residual_", new_colname, args$I), plot = mod_res$residplot, path = args$Output)
            ggsave(paste0("QQ_", new_colname, args$I), plot = mod_res$qqplot, path = args$Output)
          } else {
            ggsave(paste0("Residual_", new_colname, args$I), plot = mod_res$residplot, path = paste0(args$Output, "/StatResults/"))
            ggsave(paste0("QQ_", new_colname, args$I), plot = mod_res$qqplot, path = paste0(args$Output, "/StatResults/"))
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
  
  ## Calculate some basic univariate statistics
  basic_stat <- function(x, dat) {
    sumstat <- c(summary(dat[[x]])[1:6], sd(dat[[x]], na.rm = TRUE))
    names(sumstat)[7] <- "Std. Dev"
    return(sumstat)
  }
  b_stat <- sapply(response_vars, basic_stat, dat = tbl0)
  # Save basic statistics results to Excel.
  if(exists("dirtest") && (class(dirtest) == "try-error")){
    try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/stat_res.xlsx"), row.names=TRUE))
    try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/tukey_res.xlsx"), row.names=TRUE))
    try(openxlsx::write.xlsx(b_stat, file=paste0(args$Output, "/stat_basic.xlsx"), row.names=TRUE))
  } else {
    try(openxlsx::write.xlsx(mod_res_list_save, file=paste0(args$Output, "/StatResults/stat_res.xlsx"), row.names=TRUE))
    try(openxlsx::write.xlsx(tukey_res_list_save, file=paste0(args$Output, "/StatResults/tukey_res.xlsx"), row.names=TRUE))
    try(openxlsx::write.xlsx(b_stat, file=paste0(args$Output, "/StatResults/stat_basic.xlsx"), row.names=TRUE))
  }
  # Memory clearing
  rm(mod_res_list_save)
  rm(tukey_res_list_save)
  rm(b_stat)
}




# Savepoint
save_atp <- try(save.image(file=paste0(args$Output, "/myEnv_",format(Sys.time(),'%Y%m%d_%H%M%S'),".RData")))
if(class(save_atp) == "try-error") {save.image(file=paste0("./myEnv_", format(Sys.time(),'%Y%m%d_%H%M%S'),".RData"))}
