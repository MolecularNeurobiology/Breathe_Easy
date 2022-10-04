required_libs <- c("rjson", "tidyverse", "magrittr", "data.table",
                   "ggpubr", "kableExtra", "rmarkdown", "argparser",
                   "lme4", "lmerTest", "multcomp", "xtable", 
                   "tidyselect", "ggthemes", "RColorBrewer", "openxlsx")

for(libb in required_libs){
  lib_test <- eval(parse(text = paste0("require(", libb, ")")))
  if(!lib_test){
    install.packages(libb, dependencies = TRUE)
    lib_test_install <- eval(parse(text = paste0("require(", libb, ")")))
    if(!lib_test_install & libb == "rjson"){
      install.packages("http://cran.r-project.org/src/contrib/Archive/rjson/rjson_0.2.20.tar.gz",
                       repos = NULL, type = "source")
    }
  }
}

setwd("Z:/Projects/PM101_ST_APP_TTA_Longitudinal_Respiratory_Study/Final Files/BASSPRO_output/")

mousers <- unique(tbl0$Mouse_And_Session_ID)
cons <- unique(tbl0$Condition)
res <- c("OxygenConsumption","VO2")
which <- c("all")

for (r in res){
  print(r)
  if(!dir.exists(paste0(r,"/"))){
    dirtest <- try(dir.create(paste0(r,"/")))
  } 
  for (c in cons){
    print(c)
    if(!dir.exists(paste0(r,"/",c,"/")%>%str_replace_all("%",""))){
      dirtest <- try(dir.create(paste0(r,"/",c,"/")%>%str_replace_all("%","")))
    } 
  }
}
for (r in res){
  print(r)
  for (c in cons){
    print(c)
    if(c == "Room Air"){
      if(which == "all"){
        print("all")
        jpeg(filename = paste0("./",r,"/",c,"/","_",r,"_",c,"_all.jpeg")%>%str_replace_all("%",""))
        hist((tbl0%>%dplyr::filter(Condition == c))[[r]],labels = T,breaks = 20,main = paste0(c," ",r))
        dev.off()
      }else if(which == "each"|"both"){
        print("each oboth")
        for (x in mousers){
          if(x != "M17885_Ply1184"){
            jpeg(filename = paste0("./",r,"/",c,"/",x,"_",r,"_",c,".jpeg")%>%str_replace_all("%",""))
            print(x)
            hist((tbl0%>%dplyr::filter(Mouse_And_Session_ID == x,Condition == c))[[r]],labels = T,breaks = 20,main = paste0(x," ",c," ",r))
            dev.off()
          }
        }
      }
    }else{
      if(which == "all"){
        jpeg(filename = paste0("./",r,"/",c,"/","_",r,"_",c,"_all.jpeg")%>%str_replace_all("%",""))
        hist((tbl0%>%dplyr::filter(Condition == c))[[r]],labels = T,breaks = 20,main = paste0(c," ",r))
        dev.off()
      }else if(which == "each" | "both"){
        for (x in mousers){
          if(x %in% c("M17885_Ply1184","M17912_Ply1259","M17911_Ply1257","M17911_Ply1024","M17897_Ply1548","M17894_Ply1444","M17891_Ply983","M17891_Ply1313","M17891_Ply1157","M17885_Ply1251","M17868_Ply1027","M17869_Ply1046","M17874_Ply1041","M17874_Ply1274","M17881_Ply1008","M17882_Ply1252")){
            #print(x)
          }else{
            jpeg(filename = paste0("./",r,"/",c,"/",x,"_",r,"_",c,".jpeg")%>%str_replace_all("%",""))
            print(x)
            hist((tbl0%>%dplyr::filter(Mouse_And_Session_ID == x,Condition == c))[[r]],labels = T,breaks = 20,main = paste0(x," ",c," ",r))
            dev.off()
          }
        }
      }
    }
  }
}
