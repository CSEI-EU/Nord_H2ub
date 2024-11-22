cat("\014")
rm(list = ls())
graphics.off()

setwd("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/03_output_data/03_runs_paper_energy_2024")

#Packages
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

#Import data
{
  base = as.data.frame(read_excel("02_output_prepared/output_base_10op_run.xlsx", sheet = "LCOE"))
  
  elprice10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_10pdown_run.xlsx", sheet = "LCOE"))
  #elprice05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_05pdown_run.xlsx", sheet = "LCOE"))
  #elprice05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_05pup_run.xlsx", sheet = "LCOE"))
  elprice10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_10pup_run.xlsx", sheet = "LCOE"))
  
  wacc10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_10pdown_run.xlsx", sheet = "LCOE"))
  #wacc05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_05pdown_run.xlsx", sheet = "LCOE"))
  #wacc05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_05pup_run.xlsx", sheet = "LCOE"))
  wacc10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_10pup_run.xlsx", sheet = "LCOE"))
  
  lifetime10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_10pdown_run.xlsx", sheet = "LCOE"))
  #lifetime05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_05pdown_run.xlsx", sheet = "LCOE"))
  #lifetime05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_05pup_run.xlsx", sheet = "LCOE"))
  lifetime10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_10pup_run.xlsx", sheet = "LCOE"))
  
  variance10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_10pdown_run.xlsx", sheet = "LCOE"))
  #variance05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_05pdown_run.xlsx", sheet = "LCOE"))
  #variance05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_05pup_run.xlsx", sheet = "LCOE"))
  variance10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_10pup_run.xlsx", sheet = "LCOE"))
}

# Combined into separate dfs + _PV deleted (for now)
elprice = rbind(elprice10pdown, base, elprice10pup) #include 5% when run
elprice = elprice %>% 
  filter(!grepl('_PV', run_name))

wacc = rbind(wacc10pdown, base, wacc10pup) #include 5% when run
wacc = wacc %>% 
  filter(!grepl('_PV', run_name))

lifetime = rbind(lifetime10pdown, base, lifetime10pup) #include 5% when run
lifetime = lifetime %>% 
  filter(!grepl('_PV', run_name))

variance = rbind(variance10pdown, base, variance10pup) #include 5% when run
variance = variance %>% 
  filter(!grepl('_PV', run_name))

# Combined into one df
data = setNames(data.frame(matrix(ncol = 5, nrow = 3)), c("percent", "elprice", "wacc", "lifetime", "variance"))
data$percent = c("-10%", "0", "10%") #add -5% and 5%
data$elprice = elprice$`LCOE [Euro/t]`
data$wacc = wacc$`LCOE [Euro/t]`
data$lifetime = lifetime$`LCOE [Euro/t]`
data$variance = variance$`LCOE [Euro/t]`
data$percent <- as.numeric(gsub("%", "", data$percent))

# Graph
max.lcoe = max(data$elprice, data$wacc, data$lifetime)
min.lcoe = min(data$elprice, data$wacc, data$lifetime)

plot = ggplot(data, aes(x = percent, group = 1)) +
  geom_line(aes(y = elprice, color = "Electricity price"), linewidth = 1) +
  geom_point(aes(y = elprice, color = "Electricity price"), size = 3) +
  geom_line(aes(y = wacc, color = "WACC"), linewidth = 1) +
  geom_point(aes(y = wacc, color = "WACC"), size = 3) +
  geom_line(aes(y = lifetime, color = "Lifetime"), linewidth = 1) + 
  geom_point(aes(y = lifetime, color = "Lifetime"), size = 3) +
  geom_line(aes(y = variance, color = "El. price variance"), linewidth = 1) + 
  geom_point(aes(y = variance, color = "El. price variance"), size = 3) +
  scale_y_continuous(
    name = "LCOE [Euro/t]",
    limits = c(0.99*min.lcoe, 1.005*max.lcoe),
    breaks = seq(min.lcoe, max.lcoe, (max.lcoe - min.lcoe)/4),
    labels = label_number(accuracy = 0.01),
  ) +
  scale_x_continuous(
    name = "Percentage change in value",  # Label for x-axis
    minor_breaks = seq(min(data$percent), max(data$percent), by = 1),  # More gridlines on x-axis
    breaks = seq(min(data$percent), max(data$percent), by = 5)  # Major breaks for the x-axis
  ) +
  theme_bw() +
  labs(color = "") +
  scale_color_manual(breaks=c("Electricity price", "WACC", "Lifetime", "El. price variance"),
                     values=c("Electricity price" = "#4967AA", "WACC" = "#52A596", "Lifetime" = "#6B1C26", "El. price variance" = "#E66A57")) +
  theme(
    axis.title.x = element_text(size = 12, face = "bold"),
    axis.text.x = element_text(face = "bold"),
    axis.title.y = element_text(color = "black", size = 12, face = "bold"),
    axis.text.y = element_text(color = "black", face = "bold"),
    panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
    panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
    legend.position = c(0.5, 0.1),
    legend.text = element_text(size = 10),
    legend.direction = "horizontal"
  )

#ggsave("04_images/sensitivities.png", plot = plot, width = 7.5, height = 4, dpi = 300)
