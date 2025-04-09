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
  data = as.data.frame(read_excel("03_results_comparison/CO2_prices.xlsx"))
}

max.cp = max(data$`Carbon Price Lower Emission`, data$`Carbon Price Lower Emission (Green Case)`)
min.cp = 0
max.eua = max(data$`CO2 Price [EUA]`)
coeff = max.cp / max.eua

#Graph range
{
  plot = ggplot(data, aes(x = factor(Year), group = 1)) +
    
    # Line for EUA
    geom_line(aes(y = coeff * `CO2 Price [EUA]`), color = "#E66A57", linewidth = 1) +
    geom_point(aes(y = coeff * `CO2 Price [EUA]`), color = "#E66A57", size = 3) +
    scale_x_discrete(
      name = "Year",
    ) +
    
    # Plot only the range as segments starting from Low_emission
    geom_segment(aes(x = as.numeric(factor(Year))-0.1, 
                     xend = as.numeric(factor(Year))-0.1, 
                     y = `Carbon Price Lower Emission`, 
                     yend = `Carbon Price Higher Emission`), 
                 color = "#4967AA", size = 1) +
    # Add feather lines
    geom_segment(aes(x = as.numeric(factor(Year)) - 0.18, 
                     xend = as.numeric(factor(Year)) - 0.02, 
                     y = `Carbon Price Higher Emission`, 
                     yend = `Carbon Price Higher Emission`), 
                 color = "#4967AA", size = 1) +
    geom_segment(aes(x = as.numeric(factor(Year)) - 0.18, 
                     xend = as.numeric(factor(Year)) - 0.02, 
                     y = `Carbon Price Lower Emission`, 
                     yend = `Carbon Price Lower Emission`), 
                 color = "#4967AA", size = 1) +
    # Plot only the range as segments starting from Low_emission
    geom_segment(aes(x = as.numeric(factor(Year))+0.1, 
                     xend = as.numeric(factor(Year))+0.1, 
                     y = `Carbon Price Lower Emission (Green Case)`, 
                     yend = `Carbon Price Higher Emission (Green Case)`), 
                 color = "#6793D6", size = 1) +
    # Add feather lines
    geom_segment(aes(x = as.numeric(factor(Year)) + 0.02, 
                     xend = as.numeric(factor(Year)) + 0.18, 
                     y = `Carbon Price Higher Emission (Green Case)`, 
                     yend = `Carbon Price Higher Emission (Green Case)`), 
                 color = "#6793D6", size = 1) +
    geom_segment(aes(x = as.numeric(factor(Year)) + 0.02, 
                     xend = as.numeric(factor(Year)) + 0.18, 
                     y = `Carbon Price Lower Emission (Green Case)`, 
                     yend = `Carbon Price Lower Emission (Green Case)`), 
                 color = "#6793D6", size = 1) +
    
    scale_y_continuous(
      name = bquote(bold("Required Carbon Price [€/t CO"[2]*"]")),
      breaks = seq(0, 5500, 1000),
      sec.axis = sec_axis(
        trans = ~ (. - 0) / coeff, 
        name = bquote(bold("Yearly Average EUA [€/t CO"[2]*"]")),
      )
    ) +
    labs(x = "Year") +
    theme_bw() +
    scale_fill_manual(name = "", 
                      breaks = c("Range of Required Carbon Prices"),
                      values = c("Range of Required Carbon Prices" = "#4967AA")) +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "black", size = 12, face = "bold"),
      axis.text.y = element_text(color = "black", face = "bold"),
      axis.title.y.right = element_text(color = "#E66A57", size = 12, face = "bold"),
      axis.text.y.right = element_text(color = "#E66A57", face = "bold"),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
      legend.position = c(0.5, -0.09),
      legend.text = element_text(size = 8),
      legend.direction = "horizontal"
    )
  plot
  #ggsave("04_images/carbonprices_new.png", plot = plot, width = 7.5, height = 4.5, dpi = 300)
}

