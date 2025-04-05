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
  data_february = as.data.frame(read_excel("03_results_comparison/output_example_weeks.xlsx", sheet = "week february"))
  data_april = as.data.frame(read_excel("03_results_comparison/output_example_weeks.xlsx", sheet = "week april"))
  
  data_february$time = as.POSIXct(data_february$...1, format = "%Y-%m-%dT%H:%M:%S")
  data_february$date <- as.Date(data_february$time)
  
  data_april$time = as.POSIXct(data_april$...1, format = "%Y-%m-%dT%H:%M:%S")
  data_april$date <- as.Date(data_april$time)
}


#Plots
#February
{
  plot.february = ggplot(data_february, aes(x = time, group = 1)) +
    geom_line(aes(y = Constant, color = "1 op"), linewidth = 1) +
    geom_line(aes(y = `10 op`, color = "10 op"), linewidth = 1) + 
    scale_y_continuous(
      name = "Electrolyzer [MW]",
      labels = label_number(accuracy = 0.01),
    ) +
    scale_x_datetime(
      name = "Time",  # Label for x-axis
      date_breaks = "1 day",  # Breaks every day
      date_labels = "%b %d"
    ) +
    theme_bw() +
    labs(color = "") +
    scale_color_manual(breaks=c("1 op", "10 op"),
                       values=c("1 op" = "#6793D6", "10 op" = "#242E70")) +
    theme(
      axis.title.x = element_text(color = "black", size = 15, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold", size = 10),
      axis.title.y = element_text(color = "black", size = 15, face = "bold"),
      axis.text.y = element_text(color = "black", face = "bold"),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
      legend.position = c(0.875, -0.09),
      legend.text = element_text(size = 10, face="bold"),
      legend.background=element_rect(fill = alpha("white", 0)),
      legend.direction = "horizontal"
    )
  plot.february
  ggsave("04_images/variable_efficiency_february.png", plot = plot.february, width = 7, height = 4, dpi = 300)
}

#April
{
  plot.april = ggplot(data_april, aes(x = time, group = 1)) +
    geom_line(aes(y = Constant, color = "1 op"), linewidth = 1) +
    geom_line(aes(y = `10 op`, color = "10 op"), linewidth = 1) + 
    scale_y_continuous(
      name = "Electrolyzer [MW]",
      labels = label_number(accuracy = 0.01),
    ) +
    scale_x_datetime(
      name = "Time",  # Label for x-axis
      date_breaks = "1 day",  # Breaks every day
      date_labels = "%b %d"
    ) +
    theme_bw() +
    labs(color = "") +
    scale_color_manual(breaks=c("1 op", "10 op"),
                       values=c("1 op" = "#6793D6", "10 op" = "#242E70")) +
    theme(
      axis.title.x = element_text(color = "black", size = 15, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold", size = 10),
      axis.title.y = element_text(color = "black", size = 15, face = "bold"),
      axis.text.y = element_text(color = "black", face = "bold"),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
      legend.position = c(0.875, -0.09),
      legend.text = element_text(size = 10, face="bold"),
      legend.background=element_rect(fill = alpha("white", 0)),
      legend.direction = "horizontal"
    )
  plot.april
  ggsave("04_images/variable_efficiency_april.png", plot = plot.april, width = 7, height = 4, dpi = 300)
}

