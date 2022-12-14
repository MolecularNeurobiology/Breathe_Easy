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
# Additionally, it provides the methods to parse the command line arguments and loads all required libraries.
print("Setting pipeline")

#########################
####### LIBRARIES #######
#########################

#Loads required libraries for all following R scripts into the R environment. 
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

################### Adds arguments that are inserted to the terminal for file locations ####################
# Adds arguments that are inserted to the terminal for file locations.
# Arguments to be defined in the command line call; these are read via the add_argument function.

p <- arg_parser("Run STAGG")

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
args <- parse_args(p)


################### Designates location and names of the following R source codes to run ####################
starting_wd = getwd()
source(args$Tibblemaker)
setwd(starting_wd)
source(args$Stat)
source(args$Makegraph)
source(args$Bodytemp)

# Post-run cleanup
rm(list = ls())
