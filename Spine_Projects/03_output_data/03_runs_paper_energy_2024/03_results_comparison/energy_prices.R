cat("\014")
rm(list = ls())
graphics.off()

setwd("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/01_input_data/01_input_raw/energy_prices")

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
  data = as.data.frame(read_excel("2019-2050.xlsx"))
  data$...1 <- as.POSIXct(data$...1, format = "%Y-%m-%dT%H:%M:%S")
}


#Plot
{
  plot = ggplot(data, aes(x = ...1, group = 1)) +
    geom_line(aes(y = `2019`, color = "2019"), linewidth = 0.9) +
    geom_line(aes(y = `2050`, color = "2050"), linewidth = 0.9) + 
    scale_y_continuous(
      name = "Power Price [€/MWh]",
      labels = label_number(accuracy = 0.01),
    ) +
    scale_x_datetime(
      name = "Time",
      date_breaks = "1 month",
      date_labels = "%b"
    ) +
    theme_bw() +
    labs(color = "") +
    scale_color_manual(breaks=c("2019", "2050"),
                       values=c("2019" = "#242E70", "2050" = "#6793D6")) +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "black", size = 12, face = "bold"),
      axis.text.y = element_text(color = "black", face = "bold"),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
      legend.position = c(0.5, -0.106),
      legend.text = element_text(size = 10),
      legend.direction = "horizontal"
    )
  plot
  ggsave("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/03_output_data/03_runs_paper_energy_2024/04_images/powerprices.png", plot = plot, width = 9, height = 4, dpi = 300)
}
