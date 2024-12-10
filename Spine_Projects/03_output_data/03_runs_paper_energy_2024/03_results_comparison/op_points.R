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
}


#Import data
{
  data_op01 = as.data.frame(read_excel("02_output_prepared/output_base_1op_run.xlsx", sheet = "LCOE"))
  data_op02 = as.data.frame(read_excel("02_output_prepared/output_base_2op_run.xlsx", sheet = "LCOE"))
  data_op03 = as.data.frame(read_excel("02_output_prepared/output_base_3op_run.xlsx", sheet = "LCOE"))
  data_op04 = as.data.frame(read_excel("02_output_prepared/output_base_4op_run.xlsx", sheet = "LCOE"))
  data_op05 = as.data.frame(read_excel("02_output_prepared/output_base_5op_run.xlsx", sheet = "LCOE"))
  data_op06 = as.data.frame(read_excel("02_output_prepared/output_base_6op_run.xlsx", sheet = "LCOE"))
  data_op07 = as.data.frame(read_excel("02_output_prepared/output_base_7op_run.xlsx", sheet = "LCOE"))
  data_op08 = as.data.frame(read_excel("02_output_prepared/output_base_8op_run.xlsx", sheet = "LCOE"))
  data_op09 = as.data.frame(read_excel("02_output_prepared/output_base_9op_run.xlsx", sheet = "LCOE"))
  data_op10 = as.data.frame(read_excel("02_output_prepared/output_base_10op_run.xlsx", sheet = "LCOE"))
}

# Combine into df
combined_df = rbind(data_op01, data_op02, data_op03, data_op04, data_op05, data_op06, data_op07, data_op08, data_op09, data_op10)

# Delete _PV
lcoe = combined_df %>% 
  filter(!grepl('_PV', run_name))
names(lcoe)[names(lcoe) == "LCOE [Euro/t]"] <- "LCOE_Euro_t"
lcoe$op_points = sub('.....', '', lcoe$run_name)
lcoe$op_points = ifelse(lcoe$op_points != "10op", paste0("0", lcoe$op_points), lcoe$op_points)
lcoe$hours = c(0.5333, 0.6800, 1.4489, 1.25, 1.55, 2.3200, 2.5019, 3.1333, 3.3828, 4.950)

#LCOE 
ggplot(lcoe, aes(x = op_points, y = LCOE_Euro_t)) +
  geom_point() +
  labs(x = "# operating points", y = "LCOE [Euro/t]") +
  ylim(0.9995*min(lcoe$LCOE_Euro_t), 1.0005*max(lcoe$LCOE_Euro_t)) +
  theme_bw()

#Hours
ggplot(lcoe, aes(x = op_points, y = hours)) +
  geom_point(shape=16, color = "#4967AA", size=2.5) +
  labs(x = "Number of operating points", y = "Hours") +
  ylim(0, NA) + 
  theme_bw() 

number = c(1:10)
max.lcoe = max(lcoe$LCOE_Euro_t)
min.lcoe = min(lcoe$LCOE_Euro_t)
max.hours = max(lcoe$hours)
coeff = (1.0005*max.lcoe - 0.9995*min.lcoe) / max.hours

#Combined
plot = ggplot(lcoe, aes(x = number, group = 1)) +
  geom_line(aes(y = LCOE_Euro_t), color = "#4967AA", linewidth = 1) +
  geom_point(aes(y = LCOE_Euro_t), color = "#4967AA", size = 3) +
  geom_line(aes(y = 0.9995*min.lcoe + coeff  * hours), color = "#52A596", linewidth = 1) +
  geom_point(aes(y = 0.9995*min.lcoe + coeff  * hours), color = "#52A596", size = 3) +
  scale_x_continuous(
    name = "Number of operating points",
    breaks = seq(0, 10, by = 1)
  ) +
  scale_y_continuous(
    name = "LCOE [Euro/t]",
    limits = c(0.9995*min.lcoe, 1.0005*max.lcoe),
    breaks = seq(min.lcoe, max.lcoe, (max.lcoe - min.lcoe)/4),
    labels = label_number(accuracy = 0.01),
    sec.axis = sec_axis(
      trans = ~ (. - 0.9995*min.lcoe) / coeff, 
      name = "Simulation time (h)",
      breaks = c(0, 1, 2, 3, 4, 5, 6, 7)
      )
  ) +
  labs(x = "Number of operating points") +
  theme_bw() +
  theme(
    axis.title.x = element_text(size = 12, face = "bold"),
    axis.text.x = element_text(face = "bold"),
    axis.title.y = element_text(color = "#4967AA", size = 12, face = "bold"),
    axis.text.y = element_text(color = "#4967AA", face = "bold"),
    axis.title.y.right = element_text(color = "#52A596", size = 12, face = "bold"),
    axis.text.y.right = element_text(color = "#52A596", face = "bold"),
    panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
    panel.grid.minor = element_line(color = "gray98", linewidth = 0.5)
  )
plot
#ggsave("04_images/op_points.png", plot = plot, width = 7.5, height = 4, dpi = 300)
