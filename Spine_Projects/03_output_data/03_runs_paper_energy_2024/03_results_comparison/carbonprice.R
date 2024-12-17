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
  data = as.data.frame(read_excel("03_results_comparison/carbonprice.xlsx"))
}


#Graph
{
  max.cp = max(data$Low_emission)
  min.cp = 0
  max.eua = max(data$EUAs)
  coeff = max.cp / max.eua
  
  #Combined
  plot = ggplot(data, aes(x = factor(Year), group = 1)) +
    geom_bar(aes(y = Low_emission, fill = "Min Emission of Fossil Based Methanol"), stat = "identity", width = 0.6, alpha = 0.8) +
    geom_bar(aes(y = High_emission, fill = "Max Emission of Fossil Based Methanol"), stat = "identity", width = 0.6, alpha = 0.8) +
    geom_line(aes(y = coeff  * EUAs), color = "#50A192", linewidth = 1) +
    geom_point(aes(y = coeff  * EUAs), color = "#50A192", size = 3) +
    scale_x_discrete(
      name = "Year",
    ) +
    scale_y_continuous(
      name = "Required Carbon Price [Euro/t CO2]",
      breaks = seq(0, 4000, 500),
      #labels = label_number(accuracy = 0.01),
      sec.axis = sec_axis(
        trans = ~ (. - 0) / coeff, 
        name = "Yearly Average EUA [Euro/t CO2]"
      )
    ) +
    labs(x = "Year") +
    theme_bw() +
    scale_fill_manual(name = "", 
                      breaks = c("Min Emission of Fossil Based Methanol", "Max Emission of Fossil Based Methanol"),
                      values=c("Min Emission of Fossil Based Methanol" = "#242E70", "Max Emission of Fossil Based Methanol" = "#B6DBE2")) +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "black", size = 12, face = "bold"),
      axis.text.y = element_text(color = "black", face = "bold"),
      axis.title.y.right = element_text(color = "#50A192", size = 12, face = "bold"),
      axis.text.y.right = element_text(color = "#50A192", face = "bold"),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
      legend.position = c(0.5, -0.09),
      legend.text = element_text(size = 8),
      legend.direction = "horizontal"
    )
  plot
  ggsave("04_images/carbonprices.png", plot = plot, width = 7.5, height = 4.5, dpi = 300)
}

