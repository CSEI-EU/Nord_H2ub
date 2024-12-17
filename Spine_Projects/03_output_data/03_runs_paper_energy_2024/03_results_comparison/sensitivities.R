cat("\014")
rm(list = ls())
graphics.off()

#Change to your wd
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
  base = as.data.frame(read_excel("02_output_prepared/output_base_10op_run.xlsx", sheet = "LCOE"))
  
  demand10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_demand_10pdown_run.xlsx", sheet = "LCOE"))
  demand05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_demand_05pdown_run.xlsx", sheet = "LCOE"))
  demand05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_demand_05pup_run.xlsx", sheet = "LCOE"))
  demand10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_demand_10pup_run.xlsx", sheet = "LCOE"))
  
  dhprice10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_dhprice_10pdown_run.xlsx", sheet = "LCOE"))
  dhprice05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_dhprice_05pdown_run.xlsx", sheet = "LCOE"))
  dhprice05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_dhprice_05pup_run.xlsx", sheet = "LCOE"))
  dhprice10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_dhprice_10pup_run.xlsx", sheet = "LCOE"))
  
  elprice10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_10pdown_run.xlsx", sheet = "LCOE"))
  elprice05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_05pdown_run.xlsx", sheet = "LCOE"))
  elprice05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_05pup_run.xlsx", sheet = "LCOE"))
  elprice10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elprice_10pup_run.xlsx", sheet = "LCOE"))
  
  wacc10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_10pdown_run.xlsx", sheet = "LCOE"))
  wacc05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_05pdown_run.xlsx", sheet = "LCOE"))
  wacc05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_05pup_run.xlsx", sheet = "LCOE"))
  wacc10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_WACC_10pup_run.xlsx", sheet = "LCOE"))
  
  lifetime10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_10pdown_run.xlsx", sheet = "LCOE"))
  lifetime05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_05pdown_run.xlsx", sheet = "LCOE"))
  lifetime05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_05pup_run.xlsx", sheet = "LCOE"))
  lifetime10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_lifetime_10pup_run.xlsx", sheet = "LCOE"))
  
  variance10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_10pdown_run.xlsx", sheet = "LCOE"))
  variance05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_05pdown_run.xlsx", sheet = "LCOE"))
  variance05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_05pup_run.xlsx", sheet = "LCOE"))
  variance10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_elpricevar_10pup_run.xlsx", sheet = "LCOE"))
  
  invc10pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_invc_10pdown_run.xlsx", sheet = "LCOE"))
  invc05pdown = as.data.frame(read_excel("02_output_prepared/output_sens_10op_invc_05pdown_run.xlsx", sheet = "LCOE"))
  invc05pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_invc_05pup_run.xlsx", sheet = "LCOE"))
  invc10pup = as.data.frame(read_excel("02_output_prepared/output_sens_10op_invc_10pup_run.xlsx", sheet = "LCOE"))
}


# Combined into separate dfs + _PV deleted (for now)
{
  demand = rbind(demand10pdown, demand05pdown, base, demand05pup, demand10pup) 
  demand = demand %>% 
    filter(!grepl('_PV', run_name))
  
  elprice = rbind(elprice10pdown, elprice05pdown, base, elprice05pup, elprice10pup)
  elprice = elprice %>% 
    filter(!grepl('_PV', run_name))
  
  wacc = rbind(wacc10pdown, wacc05pdown, base, wacc05pup, wacc10pup)
  wacc = wacc %>% 
    filter(!grepl('_PV', run_name))
  
  lifetime = rbind(lifetime10pdown, lifetime05pdown, base, lifetime05pup, lifetime10pup)
  lifetime = lifetime %>% 
    filter(!grepl('_PV', run_name))
  
  variance = rbind(variance10pdown, variance05pdown, base, variance05pup, variance10pup)
  variance = variance %>% 
    filter(!grepl('_PV', run_name))
  
  invc = rbind(invc10pdown, invc05pdown, base, invc05pup, invc10pup)
  invc = invc %>% 
    filter(!grepl('_PV', run_name))
  
  dhprice = rbind(dhprice10pdown, dhprice05pdown, base, dhprice05pup, dhprice10pup)
  dhprice = dhprice %>% 
    filter(!grepl('_PV', run_name))

}


#Combine into one cleaned df
{
  # Combined into one df
  data = setNames(data.frame(matrix(ncol = 7, nrow = 5)), c("percent", "elprice", "wacc", "lifetime", "invc", "dhprice", "elpricevar"))
  data$percent = c("-10%", "-5%", "0", "5%", "10%")
  data$demand = demand$`LCOE [Euro/t]`
  data$elprice = elprice$`LCOE [Euro/t]`
  data$wacc = wacc$`LCOE [Euro/t]`
  data$lifetime = lifetime$`LCOE [Euro/t]`
  data$variance = variance$`LCOE [Euro/t]`
  data$invc = invc$`LCOE [Euro/t]`
  data$dhprice = dhprice$`LCOE [Euro/t]`
  data$percent <- as.numeric(gsub("%", "", data$percent))
  
}


# Graph investment
{
  max.lcoe = max(data$wacc, data$lifetime, data$invc, data$elprice, data$dhprice, data$variance, data$demand) 
  min.lcoe = min(data$wacc, data$lifetime, data$invc, data$elprice, data$dhprice, data$variance, data$demand)
  
  plot.inv = ggplot(data, aes(x = percent, group = 1)) +
    geom_line(aes(y = wacc, color = "WACC"), linewidth = 1) +
    geom_point(aes(y = wacc, color = "WACC"), size = 3) +
    geom_line(aes(y = lifetime, color = "Lifetime"), linewidth = 1) + 
    geom_point(aes(y = lifetime, color = "Lifetime"), size = 3) +
    geom_line(aes(y = invc, color = "Investment costs"), linewidth = 1) + 
    geom_point(aes(y = invc, color = "Investment costs"), size = 3) +
    geom_line(aes(y = demand, color = "Demand"), linewidth = 1) + 
    geom_point(aes(y = demand, color = "Demand"), size = 3) +
    scale_y_continuous(
      name = "LCOE [Euro/t]",
      limits = c(0.99*min.lcoe, 1.005*max.lcoe),
      breaks = seq(min.lcoe, max.lcoe, (max.lcoe - min.lcoe)/4),
      labels = label_number(accuracy = 0.01),
    ) +
    scale_x_continuous(
      name = "Percentage change in value",  # Label for x-axis
      minor_breaks = seq(min(data$percent), max(data$percent), by = 1),
      breaks = seq(min(data$percent), max(data$percent), by = 5)
    ) +
    theme_bw() +
    labs(color = "") +
    scale_color_manual(breaks=c("WACC", "Lifetime", "Investment costs", "Demand"),
                       values=c("WACC" = "#4967AA", "Lifetime" = "#52A596", "Investment costs" = "#E66A57", "Demand" = "yellow")) +
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
  plot.inv
  #ggsave("04_images/sensitivities_inv.png", plot = plot.inv, width = 7.5, height = 5, dpi = 300)
}


# Graph prices
{
  plot.price = ggplot(data, aes(x = percent, group = 1)) +
    geom_line(aes(y = elprice, color = "Electricity price"), linewidth = 1) +
    geom_point(aes(y = elprice, color = "Electricity price"), size = 3) +
    geom_line(aes(y = dhprice, color = "District heating price"), linewidth = 1) + 
    geom_point(aes(y = dhprice, color = "District heating price"), size = 3) +
    geom_line(aes(y = variance, color = "Electricity price variance"), linewidth = 1) + 
    geom_point(aes(y = variance, color = "Electricity price variance"), size = 3) +
    scale_y_continuous(
      name = "LCOE [Euro/t]",
      limits = c(0.99*min.lcoe, 1.005*max.lcoe),
      breaks = seq(min.lcoe, max.lcoe, (max.lcoe - min.lcoe)/4),
      labels = label_number(accuracy = 0.01)
    ) +
    scale_x_continuous(
      name = "Percentage change in value",  # Label for x-axis
      minor_breaks = seq(min(data$percent), max(data$percent), by = 1),  # More gridlines on x-axis
      breaks = seq(min(data$percent), max(data$percent), by = 5)  # Major breaks for the x-axis
    ) +
    theme_bw() +
    labs(color = "") +
    scale_color_manual(breaks=c("Electricity price", "Electricity price variance", "District heating price"),
                       values=c("Electricity price" = "#4967AA", "Electricity price variance" = "#52A596", "District heating price" = "#E66A57")) +
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
  plot.price
  #ggsave("04_images/sensitivities_prices.png", plot = plot.price, width = 7.5, height = 5, dpi = 300)
  
}
