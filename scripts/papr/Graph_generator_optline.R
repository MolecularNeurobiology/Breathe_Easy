

print("Preparing graphs")
# library(tidyverse)


# Graphing function
graph_make <- function(resp_var, xvar, pointdodge, facet1, facet2, 
                      graph_data, tukey_res, inter_vars,
                      savename, other = FALSE, resp_name = "", 
                      xvar_name = "", pointdodge_name = "",
                      yax_min = NA, yax_max = NA) {
  
  #Sets color palette for graphs.
  cPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")
  # Create new variable strings for graphing 
  ## If there is no value set for xvar, set to empty string for graphing below.
  if (xvar == ""){
    xvar_g <- "Nullx"
  } else {
    xvar_g <- xvar
  }
  
  ## If there is no value set for pointdodge, set to NULL for graphing below.
  if (pointdodge == ""){
    pointdodge_g <- NULL
    pointdodge_g2 <- "Nullpd"
  } else {
    pointdodge_g <- pointdodge
    pointdodge_g2 <- pointdodge
  }
  
  ## If there is no value set for facet vars, set to '.' for graphing below.
  if (facet1 == ""){
    facet1_g <- "."
  } else {
    facet1_g <- facet1
  }
  if (facet2 == ""){
    facet2_g <- "."
  } else {
    facet2_g <- facet2
  }
  
  graph_data$Nullx <- factor(1)
  graph_data$Nullpd <- factor(1)
  # Variable to denote which points should be connected
  graph_data$grouppath <- interaction(graph_data$MUID, graph_data[[xvar_g]])
  # Calculate where points in x should be
  graph_data$linex <- as.numeric(graph_data[[xvar_g]]) - 0.5 +
    seq(0, 1, length.out = (nlevels(graph_data[[pointdodge_g2]]) + 2))[-c(1, nlevels(graph_data[[pointdodge_g2]]) + 2)][
      as.numeric(graph_data[[pointdodge_g2]])]
  graph_data$xmin <- as.numeric(graph_data[[xvar_g]]) - 0.5
  graph_data$xmax <- as.numeric(graph_data[[xvar_g]]) + 0.5
  
  # Arrange graph_df for drawing line segments
  graph_data <- graph_data %>%
    dplyr::arrange(linex)
  
  #Facet code string generation
  form_string <- as.formula(paste0(facet2_g, " ~ ", facet1_g))
  
  p <- ggplot() +
    geom_blank(aes_string(x = xvar_g, y = resp_var), data = graph_data) +
    facet_grid(form_string, scales = "fixed") + 
    theme_few() 
  
  p <- p + geom_path(aes_string(x = "linex", y = resp_var, group = "grouppath"), data = graph_data,
                     alpha = 0.3, linetype = 'twodash')
  
  # if(!other){
  #   p <- p + geom_path(aes_string(x = "linex", y = resp_var, group = "grouppath"), data = graph_data,
  #             alpha = 0.3, linetype = 'twodash')
  # }
  
  if(pointdodge != "") {
    p <- p + 
      geom_point(aes_string(x = "linex", y = resp_var, fill = pointdodge_g), data = graph_data,
                        pch = 21, stroke = 1) + 
      scale_fill_manual(values=cPalette)
  } else {
    p <- p + 
      geom_point(aes_string(x = "linex", y = resp_var, fill = pointdodge_g), data = graph_data,
                        show.legend = FALSE, pch = 21, stroke = 1) + 
      scale_fill_manual(values= "black")
  }
  
  if(xvar != ""){
    p <- p + 
      theme(axis.text.x = element_text(angle = -45, hjust = 0)) 
  } else {
    p <- p + 
      theme(axis.text.x = element_blank(), axis.title.x = element_blank()) 
  }

  # Errorbar and mean point locations
  box_vars <- c(xvar, pointdodge, facet1, facet2)
  box_vars <- box_vars[box_vars != ""]
  
  box_graph_df <- graph_data %>%
    group_by_at(box_vars) %>%
    dplyr::summarise(mid = mean(eval(parse(text = resp_var)), na.rm = TRUE),
                     sds = sd(eval(parse(text = resp_var)), na.rm = TRUE),
                     linex = mean(linex, na.rm = TRUE),
                     ymin = min(eval(parse(text = resp_var)), na.rm = TRUE),
                     ymax = max(eval(parse(text = resp_var)), na.rm = TRUE),
                     xmin = mean(xmin, na.rm = TRUE),
                     xmax = mean(xmax, na.rm = TRUE))
  box_graph_df$alpha_x <- 0
  box_graph_df$alpha_pd <- 0
  
  # Draw errorbar and mean points
  p <- p + 
    geom_point(aes(x = linex, y = mid), data = box_graph_df,
               size = 5.5, pch = 21, stroke = 1, fill = NA) + 
    geom_errorbar(aes(x = linex, ymin = mid + sds, ymax = mid - sds), data = box_graph_df,
                  alpha = 0.5) 
  

  
  # Pointdodge lines
  pd_line_vars <- c(xvar, facet1, facet2)
  pd_line_vars <- pd_line_vars[pd_line_vars != ""]
  
  if(length(pd_line_vars) > 0){
    pd_line_graph_df <- box_graph_df %>%
      group_by_at(pd_line_vars) %>%
      dplyr::summarise(ymin = min(ymin, na.rm = TRUE),
                       ymax = max(ymax, na.rm = TRUE),
                       sdmax = max(mid + sds, na.rm = TRUE),
                       xmin = mean(xmin, na.rm = TRUE),
                       xmax = mean(xmax, na.rm = TRUE))
  } else {
    pd_line_graph_df <- box_graph_df %>%
      dplyr::summarise(ymin = min(ymin, na.rm = TRUE),
                       ymax = max(ymax, na.rm = TRUE),
                       sdmax = max(mid + sds, na.rm = TRUE),
                       xmin = mean(xmin, na.rm = TRUE),
                       xmax = mean(xmax, na.rm = TRUE))
  }
  
  pd_line_graph_df$yline <- pmax(pd_line_graph_df$ymax, pd_line_graph_df$sdmax) + max(pd_line_graph_df$ymax - pd_line_graph_df$ymin) * 0.08
  pd_line_graph_df$asty <- pd_line_graph_df$yline + max(pd_line_graph_df$ymax - pd_line_graph_df$ymin) * 0.05
  
  
  # xvar lines
  facet_vars <-  c(facet1, facet2)
  facet_vars <- facet_vars[facet_vars != ""]
  if(length(facet_vars) > 0){
    x_line_df <- pd_line_graph_df %>%
      group_by_at(facet_vars) %>%
      dplyr::summarise(y1 = max(asty), y2 = max(asty - yline),
                       xmin = min(xmin),
                       xmax = max(xmax))
  } else {
    x_line_df <- pd_line_graph_df %>%
      ungroup() %>%
      dplyr::summarise(y1 = max(asty), y2 = max(asty - yline),
                       xmin = min(xmin),
                       xmax = max(xmax))
  }
  x_line_df$yline2 <- x_line_df$y1 + x_line_df$y2 * 2
  x_line_df$asty2 <- x_line_df$yline2 + x_line_df$y2 * 1.5
  
  
  
  # To draw asterisk or not
  if(length(pd_line_vars) > 0){
    box_graph_df <- left_join(box_graph_df, pd_line_graph_df, by = pd_line_vars)
  } else {
    box_graph_df <- bind_cols(box_graph_df, pd_line_graph_df %>% slice(rep(1:n(), each = nrow(box_graph_df))))
  }
  
  if(length(facet_vars) > 0){
    box_graph_df <- left_join(box_graph_df, x_line_df, by = facet_vars)
  } else {
    box_graph_df$yline2 <- x_line_df$yline2
    box_graph_df$asty2 <- x_line_df$asty2
  }
  
  box_graph_df$astpd <- ""
  box_graph_df$astx <- ""
  
  if(pointdodge != ""){
    colorframe <- data.frame(val = levels(box_graph_df[[pointdodge]]), color = cPalette[1:nlevels(box_graph_df[[pointdodge]])])
    suppressWarnings(eval(parse(text = paste0("box_graph_df <- left_join(box_graph_df, colorframe, by = c('", pointdodge, "' = 'val'))" ))))
  }
  

  xvar_ind <- which(inter_vars == xvar)
  pd_ind <- which(inter_vars == pointdodge)
  
  for(jj in 1:nrow(box_graph_df)){
    tukey_names <- lapply(strsplit(rownames(tukey_res), "-"), trimws)
    comp_rows <- lapply(tukey_names, strsplit, split = "\\.")
    
    # Find rows from tukey list that are relevant
    relevant_row_find <- function(comp_names, comp_ind, curr_ind, sum_df, comp_var, match_var_names){
      # Remove special characters and spaces in interaction variables categories. Necessary for relevant category finding below.
      for(vv in match_var_names){
        # if(typeof(sum_df[[vv]]) == "character"){
        # sum_df[[vv]] <- sum_df[[vv]] %>% str_replace_all("[[:punct:]]", "") %>% str_replace_all(" ", "")
        sum_df[[vv]] <- sum_df[[vv]] %>% as.character() %>% str_replace_all("[[:punct:]]", "") %>% str_replace_all(" ", "")
        sum_df[[vv]] <- sapply(sum_df[[vv]], X_num) %>% unname()
        # }
      }
      
      char_df <- data.frame(lapply(sum_df, as.character), stringsAsFactors=FALSE)
      rel_bool <- (sum((char_df[curr_ind, match_var_names][-which(match_var_names == comp_var)] %in% comp_names[[1]][- comp_ind])) ==
                     (length(match_var_names) - 1)) & 
        (sum((char_df[curr_ind, match_var_names][-which(match_var_names == comp_var)] %in% comp_names[[2]][- comp_ind])) ==
           (length(match_var_names) - 1)) & 
        ((sum(comp_names[[1]][comp_ind] == char_df[jj, comp_var]) + 
            sum(comp_names[[2]][comp_ind] == char_df[jj, comp_var])) == 1)
      return(rel_bool)
    }
    
    # Match rows to the plotting data frame.
    match_row_find <- function(comp_names, curr_ind, sum_df, match_var_names){
      # Remove special characters and spaces in interaction variables categories. Necessary for relevant category finding below.
      for(vv in match_var_names){
        # if(typeof(sum_df[[vv]]) == "character"){
        # sum_df[[vv]] <- sum_df[[vv]] %>% str_replace_all("[[:punct:]]", "") %>% str_replace_all(" ", "")
        sum_df[[vv]] <- sum_df[[vv]] %>% as.character() %>% str_replace_all("[[:punct:]]", "") %>% str_replace_all(" ", "")
        sum_df[[vv]] <- sapply(sum_df[[vv]], X_num) %>% unname()
        # }
      }
    
      matchnames <- sum_df[, match_var_names]
      
      if(is.null(dim((apply(matchnames, 1, "%in%", comp_names[[1]]))))){
        m1 <- which(apply(matchnames, 1, "%in%", comp_names[[1]]))
        m2 <- which(apply(matchnames, 1, "%in%", comp_names[[2]]))
        ci <- which(c(m1, m2) == curr_ind)
        return(c(c(m1, m2)[ci], c(m1, m2)[-ci]))
      } else {
        m1 <- which(colSums(apply(matchnames, 1, "%in%", comp_names[[1]])) == length(matchnames))
        m2 <- which(colSums(apply(matchnames, 1, "%in%", comp_names[[2]])) == length(matchnames))
        ci <- which(c(m1, m2) == curr_ind)
        return(c(c(m1, m2)[ci], c(m1, m2)[-ci]))
      }
    }
    
    if(length(xvar_ind) == 1) {
      relevant_x_rows <- (unlist(lapply(comp_rows, relevant_row_find, comp_ind = xvar_ind, 
                                        curr_ind = jj, sum_df = box_graph_df, comp_var = xvar, 
                                        match_var_names = box_vars)))
      
      #################################
      if(sum(relevant_x_rows) != 0){ 
        ast_x_rows <- which(tukey_res$pvalue < 0.05 & relevant_x_rows)
        if(length(ast_x_rows) != 0) {
          box_graph_df$astx[jj] <- "*"
          box_graph_df$alpha_x[jj] <- 1
          x_lines <- lapply(comp_rows[ast_x_rows], match_row_find, curr_ind = jj, sum_df = box_graph_df,
                            match_var_names = box_vars)
          x_lines_df <- data.frame(x = box_graph_df$linex[unlist(lapply(x_lines, "[[", 1))], 
                                   y = box_graph_df$asty2[unlist(lapply(x_lines, "[[", 1))], 
                                   xend = box_graph_df$linex[unlist(lapply(x_lines, "[[", 2))], 
                                   yend = box_graph_df$yline2[unlist(lapply(x_lines, "[[", 2))])
          x_var_names <- box_graph_df[jj, box_vars, drop = FALSE] %>% slice(rep(1:n(), each = length(x_lines)))
          x_lines_df <- bind_cols(x_lines_df, x_var_names)
          if(pointdodge != ""){
            suppressWarnings(eval(parse(text = paste0("x_lines_df <- left_join(x_lines_df, colorframe, by = c('", pointdodge, "' = 'val'))" ))))
            p <- p + 
              geom_segment(aes_string(x = "x", y = "y", xend = "xend", yend = "yend", color = "color"), data = x_lines_df, show.legend = FALSE,
                           size = 0.5, alpha = 0.6, linetype = 'dotted')
          } else {
            p <- p + 
              geom_segment(aes_string(x = "x", y = "y", xend = "xend", yend = "yend"), data = x_lines_df, show.legend = FALSE,
                           size = 0.5, alpha = 0.6, linetype = 'dotted')
          }
        }
      }
    }
    
    if(length(pd_ind) == 1) {
      relevant_pd_rows <- (unlist(lapply(comp_rows, relevant_row_find, comp_ind = pd_ind, 
                                         curr_ind = jj, sum_df = box_graph_df, comp_var = pointdodge, 
                                         match_var_names = box_vars)))
      if(sum(relevant_pd_rows) != 0){
        ast_pd_rows <- which(tukey_res$pvalue < 0.05 & relevant_pd_rows)
        if(length(ast_pd_rows) != 0){
          box_graph_df$astpd[jj] <- "*"
          box_graph_df$alpha_pd[jj] <- 1
          pd_lines <- lapply(comp_rows[ast_pd_rows], match_row_find, curr_ind = jj, sum_df = box_graph_df,
                             match_var_names = box_vars)
          pd_lines_df <- data.frame(x = box_graph_df$linex[unlist(lapply(pd_lines, "[[", 1))], 
                                    y = box_graph_df$asty[unlist(lapply(pd_lines, "[[", 1))], 
                                    xend = box_graph_df$linex[unlist(lapply(pd_lines, "[[", 2))], 
                                    yend = box_graph_df$yline[unlist(lapply(pd_lines, "[[", 2))])
          pd_var_names <- box_graph_df[jj, box_vars, drop = FALSE] %>% slice(rep(1:n(), each = length(pd_lines)))
          pd_lines_df <- bind_cols(pd_lines_df, pd_var_names)
          suppressWarnings(eval(parse(text = paste0("pd_lines_df <- left_join(pd_lines_df, colorframe, by = c('", pointdodge, "' = 'val'))" ))))
          p <- p + 
            geom_segment(aes_string(x = "x", y = "y", xend = "xend", yend = "yend", color = "color"), data = pd_lines_df, show.legend = FALSE,
                         size = 0.5, alpha = 0.6, linetype = 'dotted')
        }
      }
    }
  }
  
  if(length(pd_line_vars) > 0){
    pd_alpha_graph_df <- box_graph_df %>%
      group_by_at(pd_line_vars) %>%
      dplyr::summarise(alpha_pd = max(alpha_pd))
    pd_line_graph_df <- left_join(pd_line_graph_df, pd_alpha_graph_df, by = pd_line_vars)
  } else {
    pd_alpha_graph_df <- box_graph_df %>%
      dplyr::summarise(alpha_pd = max(alpha_pd))
    pd_line_graph_df$alpha_pd <- pd_alpha_graph_df$alpha_pd
  }
  if(length(facet_vars) > 0){
    x_alpha_df <- box_graph_df %>%
      group_by_at(facet_vars) %>%
      dplyr::summarise(alpha_x = max(alpha_x))
    x_line_df <- left_join(x_line_df, x_alpha_df, by = facet_vars)
  } else {
    x_alpha_df <- box_graph_df %>%
      ungroup() %>%
      dplyr::summarise(alpha_x = max(alpha_x))
    x_line_df$alpha_x <- x_alpha_df$alpha_x
  }
  
  print(pd_line_graph_df)
  p <- p +
    geom_segment(aes(x = xmin, xend = xmax, y = yline, yend = yline, alpha = alpha_pd), data = pd_line_graph_df,
                 color = "grey") 
  print(x_line_df)
  p <- p +
    geom_segment(aes(x = xmin, xend = xmax, y = yline2, yend = yline2, alpha = alpha_x), data = x_line_df,
                 color = "grey") 
  
  
  # Drawing code
  if(pointdodge != "") {
    p <- p +
      geom_text(aes_string(x = "linex", y = "asty", label = "astpd", color = "color"),
                data = box_graph_df, size = 5, show.legend = FALSE) + 
      scale_color_identity()
    
    if(length(facet_vars) > 0){
      p <- p + geom_text(aes_string(x = "linex", y = "asty2", label = "astx", color = "color"),
                         data = box_graph_df, size = 10, show.legend = FALSE) 
    } else {
      p <- p + geom_text(aes_string(x = "linex", y = "asty2", label = "astx", color = "color"),
                         data = box_graph_df, size = 10, show.legend = FALSE) 
    }
  } else {
    p <- p +
      geom_text(aes_string(x = "linex", y = "asty", label = "astpd"),
                data = box_graph_df, size = 5, show.legend = FALSE) 
    
    if(length(facet_vars) > 0){
      p <- p + geom_text(aes_string(x = "linex", y = "asty2", label = "astx"),
                         data = box_graph_df, size = 10, show.legend = FALSE) 
    } else {
      p <- p + geom_text(aes_string(x = "linex", y = "asty2", label = "astx"),
                         data = box_graph_df, size = 10, show.legend = FALSE) 
    }
  }
  
  p <- p + labs(x = xvar_name, y = resp_name, color = pointdodge_name)
  
  if(!(is.na(yax_min)) && !(is.na(yax_max)) && !(is.null(yax_min)) && !(is.null(yax_max))) {
    p <- p + scale_y_continuous(limits = c(yax_min, yax_max), expand = expansion(mult = c(0, 0)))
  } else {
    p <- p + scale_y_continuous(limits = c(min(c(box_graph_df$ymin, box_graph_df$mid - box_graph_df$sds)), 
                                           max(c(box_graph_df$asty2, box_graph_df$mid + box_graph_df$sds))), 
                                expand = expansion(mult = c(0.035, 0.07)))
  }
  
  # print(p)
  
  # Make sure the graph is wide enough.
  x_width <- max(dev.size("cm")[1], max(length(unique(graph_data[[xvar_g]])), 1) * 
                   max(length(unique(graph_data[[pointdodge_g2]])), 1) * 
                   max(length(unique(graph_data[[facet1_g]])), 1) * 2 / 3 + 5)
  
  # Make sure the graph is tall enough.
  y_height <- max(dev.size("cm")[2], max(length(unique(graph_data[[facet2_g]])), 1) * 7.5 + 10)
  
  # Saves graphs to designated folder from user selections in GUI.
  ggsave(savename, plot = p, path = args$Output, width = x_width, height = y_height, units = "cm")
}


#### Loop to run everything
print("Making graphs")
response_var_names <- var_names$With_units[which(var_names$Dependent != 0)]
if((!is.na(response_vars)) && (!is_empty(response_vars)) && (!is.na(interaction_vars)) && (!is_empty(interaction_vars))){ 
    
  for(ii in 1:length(response_vars)){
    
    if(((is.na(transform_set[ii])) || (!("non" %in% transform_set[ii])))){
      print(paste0("Making graph for ", response_vars[ii]))
      
      graph_v <- c(xvar, pointdodge, facet1, facet2)
      graph_v <- graph_v[graph_v != ""]
      
      graph_df <- tbl0 %>%
        dplyr::filter(Breath_Inclusion_Filter == 1) %>% 
        group_by_at(c(graph_v, "MUID")) %>%
        dplyr::summarise_at(response_vars[ii], mean, na.rm = TRUE) %>%
        ungroup() %>% na.omit()
      
      
      for(mm in 1:length(graph_v)){
        v_ind <- which(graph_vars$Alias == graph_v[mm])
        if(!(is.null(graph_vars$Alias[v_ind])) && !(is.na(graph_vars$Alias[v_ind])) && (graph_vars$Alias[v_ind] != "")){
          if((!(is.null(graph_vars$Order[v_ind]))) && (!(is.na(graph_vars$Order[v_ind]))) && (graph_vars$Order[v_ind] != "")) {
            f_levels <- unlist(strsplit(graph_vars$Order[v_ind], "@"))
            f_levels <- str_trunc(f_levels, 25, side = "center", ellipsis = "___")
            if(all(f_levels %in% graph_df[[graph_vars$Alias[v_ind]]])) {
              graph_df[[graph_vars$Alias[v_ind]]] <- factor(graph_df[[graph_vars$Alias[v_ind]]], levels = f_levels)
            } else {
              graph_df[[graph_vars$Alias[v_ind]]] <- factor(graph_df[[graph_vars$Alias[v_ind]]], 
                                                            levels = unique(tbl0[[graph_vars$Alias[v_ind]]]))
            }
          } else {
            graph_df[[graph_vars$Alias[v_ind]]] <- factor(graph_df[[graph_vars$Alias[v_ind]]], 
                                                          levels = unique(tbl0[[graph_vars$Alias[v_ind]]]))
          }
        } else {
          next
        }
      }
      
      graph_file  <- paste0(response_vars[ii], args$I)
      graph_make(response_vars[ii], xvar, pointdodge, facet1, 
                 facet2, graph_df, tukey_res_list[[response_vars[ii]]], 
                 interaction_vars, graph_file, other = FALSE, 
                 response_var_names[ii], xvar_wu, pointdodge_wu,
                 yax_min = ymins[ii], yax_max = ymaxes[ii])
    }
    
    
    
    
    ##########################################
    #Makes graphs for desired transformations#
    ##########################################
    if(!is.na(transform_set[ii]) && (transform_set[ii] != "")){
      transforms_resp <- unlist(strsplit(transform_set[ii], "@"))
      for(jj in 1:length(transforms_resp)){
        new_colname <- paste0(response_vars[ii], "_", transforms_resp[jj])
        
        if(!is.null(tukey_res_list[[new_colname]])){
          graph_df <- tbl0 %>%
            dplyr::filter(Breath_Inclusion_Filter == 1) %>% 
            group_by_at(c(graph_v, "MUID")) %>%
            dplyr::summarise_at(new_colname, mean, na.rm = TRUE) %>%
            ungroup() %>% na.omit()
          
          for(mm in 1:length(graph_v)){
            v_ind <- which(graph_vars$Alias == graph_v[mm])
            if(!(is.null(graph_vars$Alias[v_ind])) && !(is.na(graph_vars$Alias[v_ind])) && (graph_vars$Alias[v_ind] != "")){
              if((!(is.null(graph_vars$Order[v_ind]))) && (!(is.na(graph_vars$Order[v_ind]))) && (graph_vars$Order[v_ind] != "")) {
                f_levels <- unlist(strsplit(graph_vars$Order[v_ind], "@"))
                f_levels <- str_trunc(f_levels, 25, side = "center", ellipsis = "___")
                if(all(f_levels %in% graph_df[[graph_vars$Alias[v_ind]]])) {
                  graph_df[[graph_vars$Alias[v_ind]]] <- factor(graph_df[[graph_vars$Alias[v_ind]]], levels = f_levels)
                } else {
                  graph_df[[graph_vars$Alias[v_ind]]] <- factor(graph_df[[graph_vars$Alias[v_ind]]], 
                                                                levels = unique(tbl0[[graph_vars$Alias[v_ind]]]))
                }
              } else {
                graph_df[[graph_vars$Alias[v_ind]]] <- factor(graph_df[[graph_vars$Alias[v_ind]]], 
                                                              levels = unique(tbl0[[graph_vars$Alias[v_ind]]]))
              }
            } else {
              next
            }
          }
          
          graph_file  <- paste0(new_colname, args$I)
          graph_make(new_colname, xvar, pointdodge, facet1, 
                     facet2, graph_df, tukey_res_list[[new_colname]], 
                     interaction_vars, graph_file, other = FALSE, 
                     response_var_names[ii], xvar_wu, pointdodge_wu)
        }
        
      }
    }
    
  }
}




