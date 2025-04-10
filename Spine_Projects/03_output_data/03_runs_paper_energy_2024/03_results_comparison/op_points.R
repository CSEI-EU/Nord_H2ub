cat("\014")
rm(list = ls())
graphics.off()

setwd("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/03_output_data/03_runs_paper_energy_2024")

#Packages
{
  library(stargazer)
  library(readxl)
  library(goeveg)
  library(readr)
  library(ivreg)
  library(car)
  library(estimatr)
  library(ggfortify)
  library(wooldridge)
  library(AER)
  library(forecast)
  library(urca)
  library(strucchange)
  library(readr)
  library(stats)
  library(tidyverse)
  library(xtable)
  library(ggplot2)
  library(scales)
  library(ggbreak)
}


#Import data
{
  data_op01 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_1op_run.xlsx", sheet = "LCOE"))
  data_op02 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_2op_run.xlsx", sheet = "LCOE"))
  data_op03 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_3op_run.xlsx", sheet = "LCOE"))
  data_op04 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_4op_run.xlsx", sheet = "LCOE"))
  data_op05 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_5op_run.xlsx", sheet = "LCOE"))
  data_op06 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_6op_run.xlsx", sheet = "LCOE"))
  data_op07 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_7op_run.xlsx", sheet = "LCOE"))
  data_op08 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_8op_run.xlsx", sheet = "LCOE"))
  data_op09 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_9op_run.xlsx", sheet = "LCOE"))
  data_op10 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_10op_run.xlsx", sheet = "LCOE"))
  data_op15 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_15op_run.xlsx", sheet = "LCOE"))
  data_op20 = as.data.frame(read_excel("02_output_prepared/review_1/output_base_20op_run.xlsx", sheet = "LCOE"))
}


# Combine into df
{
  combined_df = rbind(data_op01, data_op02, data_op03, data_op04, data_op05, data_op06, data_op07, data_op08, data_op09, data_op10, 
                      (data_op15$`LCOE [Euro/t]`[1] + data_op10$`LCOE [Euro/t]`[1])/2, 
                      data_op15, data_op20)
  
  # Delete _PV
  lcoe = combined_df %>% 
    filter(!grepl('_PV', run_name))
  names(lcoe)[names(lcoe) == "LCOE [Euro/t]"] <- "LCOE_Euro_t"
  lcoe$op_points = sub('.....', '', lcoe$run_name)
  lcoe$op_points = ifelse(!(lcoe$op_points %in% c("10op", "15op", "20op")), paste0("0", lcoe$op_points), lcoe$op_points)
  lcoe$hours = c(0.5333, 0.6800, 1.4489, 1.25, 1.55, 2.3200, 2.5019, 3.1333, 3.3828, 4.950, (19.543+4.950)/2, 19.543, 33.168)
  lcoe$hours_fake = c(0.5333, 0.6800, 1.4489, 1.25, 1.55, 2.3200, 2.5019, 3.1333, 3.3828, 4.950, (7+4.950)/2, 7, 8)
}


#Graph
{
  number = factor(c(1:11, 15, 20), levels = c(1:11, 15, 20))
  max.lcoe = max(lcoe$LCOE_Euro_t)
  min.lcoe = min(lcoe$LCOE_Euro_t)
  max.hours = max(lcoe$hours_fake)
  coeff = (1.0005*max.lcoe - 0.9995*min.lcoe) / max.hours
  
  #Combined
  plot = ggplot(lcoe, aes(x = number, group = 1)) +
    geom_line(aes(y = 0.9995*min.lcoe + coeff  * hours_fake), color = "#4967AA", linewidth = 1) +
    geom_point(aes(y = 0.9995*min.lcoe + coeff  * hours_fake), color = "#4967AA", 
               size = ifelse(number == 11, NA, 3)) +
    geom_line(aes(y = LCOE_Euro_t), color = "#6793D6", linewidth = 1) +
    geom_point(aes(y = LCOE_Euro_t), color = "#6793D6", 
               size = ifelse(number == 11, NA, 3)) + 
    
    scale_x_discrete(
      name = "Number of operating points",
      breaks = c(1:10, 15, 20),
      labels = c("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "15", "20")
    ) +
    
    # Manually add a fake "scale break" with a white rectangle
    coord_cartesian(xlim = c(NA, 13.89), ylim=c(1368, 1377), expand=FALSE, clip="off") +
    
    # Axis break x axis
    annotate("segment", x = 0, xend = 13.89, 
             y=1377, yend = 1377, color="black", linewidth =0.5) + #upper axis
    annotate("segment", x = c(0,11.15), xend = c(10.85, 13.89), 
             y=1368, yend = 1368, color="black", linewidth =0.5) + #lower axis
    annotate("segment", x = 10.75, xend = 10.95, y = 1368-0.2, yend= 1368+0.2, color = "black") +
    annotate("segment", x = 11.05, xend = 11.25, y = 1368-0.2, yend= 1368+0.2, color = "black") +
    
    # Axis break right y axis
    annotate("segment", x = 13.89, xend = 13.89, 
             y=c(1368,1374.25), yend = c(1374, 1377), color="#4967AA", linewidth =0.5) + 
    annotate("segment", x = 14.09, xend = 13.69, y = 1374-0.1, yend= 1374+0.1, color = "#4967AA") +
    annotate("segment", x = 14.09, xend = 13.69, y = 1374.25-0.1, yend= 1374.25+0.1, color = "#4967AA") +
    
    # Paint white over cross
    annotate("segment", x = 11, xend=11, y =1374, yend=1374.25, color="white", linewidth=4) +
    annotate("segment", x = 11, xend=11, y =1374.8, yend=1375.4, color="white", linewidth=4) +
    
    scale_y_continuous(
      name = bquote(bold("LCOM [€/t CH"[3]*"OH]")),
      #limits = c(0.9995*min.lcoe, 1.0005*max.lcoe),
      breaks = seq(min.lcoe, max.lcoe, (max.lcoe - min.lcoe)/4),
      labels = label_number(accuracy = 0.01),
      sec.axis = sec_axis(
        trans = ~ (. - 0.9995*min.lcoe) / coeff, 
        name = "Simulation time [h]",
        breaks = c(0, 1, 2, 3, 4, 5, 7, 8),
        labels = c("0", "1", "2", "3", "4", "5", "20", "30")
      )
    ) +
    labs(x = "Number of operating points") +
    #theme_bw() +
    theme_classic() +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "#6793D6", size = 12, face = "bold"),
      axis.text.y = element_text(color = "#6793D6", face = "bold"),
      axis.title.y.right = element_text(color = "#4967AA", size = 12, face = "bold"),
      axis.text.y.right = element_text(color = "#4967AA", face = "bold"),
      axis.line.x = element_blank(),
      axis.line.y.right = element_blank(),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5)
    )
  plot
  #ggsave("04_images/op_points.png", plot = plot, width = 7.5, height = 4, dpi = 300)
}

