# DESCRIPTION:
# pipeline.r is the main wrapper of all the scripts for papr. 
# Additionally, it provides the methods to parse the command line arguments and loads all required libraries.
print("Setting pipeline")
library(rjson)
library(tidyverse)
library(magrittr)
library(data.table)
library(ggpubr)
library(kableExtra)
library(rmarkdown)
library(argparser)
library(lme4)
library(lmerTest)
library(multcomp)
library(xtable)
library(tidyselect)
library(ggthemes)
library(RColorBrewer)
library(openxlsx)

################### Adds arguments that are inserted to the terminal for file locations ####################
# Arguments to be defined in the command line call; these are read via the add_argument function.

p <- arg_parser("Run STAGG")

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

p <- add_argument (p, "--Sum", help="Filepath to directory with R markdown code for summary html")


# Arguments are imported + stored as a list with the names defined as above.
args <- parse_args(p)


################### Designates location and names of the following R source codes to run ####################

source(args$Tibblemaker)
source(args$Stat)
source(args$Makegraph)
source(args$Bodytemp)

# Post-run cleanup
rm(list = ls())