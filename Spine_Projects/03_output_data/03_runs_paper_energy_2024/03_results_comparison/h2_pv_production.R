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
  february = as.data.frame(read_excel("03_results_comparison/output_example_weeks.xlsx", sheet = "week february"))
  february$Time <- as.POSIXct(february$Time, format = "%Y-%m-%dT%H:%M:%S")
  
  april = as.data.frame(read_excel("03_results_comparison/output_example_weeks.xlsx", sheet = "week april"))
  april$Time <- as.POSIXct(april$Time, format = "%Y-%m-%dT%H:%M:%S")
}

{
  coeff.1 = 2.5 * max(february$`10 op`, april$`10 op`) / max(february$`PV Production`, april$`PV Production`)
  coeff.2 = 0.75 * max(february$`10 op`, april$`10 op`) / max(february$`power price`,april$`power price`)
}

# February - H2 PV production
{
  #Combined
  plot.1.f = ggplot(february, aes(x = Time, group = 1)) +
    geom_line(aes(y = `10 op`), color = "#E66A57", linewidth = 1) +
    geom_line(aes(y = coeff.1  * `PV Production`), color = "#50A192", linewidth = 1) +
    
    scale_y_continuous(
      name = bquote(bold("Electrolyzer [MW]")),
      breaks = seq(0, 80, 10),
      sec.axis = sec_axis(
        trans = ~ . / coeff.1, 
        name = bquote(bold("PV [MW]")),
        breaks = seq(0,300, 50)
      )
    ) +
    scale_x_datetime(
      name = "Time",
      date_breaks = "1 day",
      date_labels = "%d/%m"
    ) +
    theme_bw() +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "#E66A57", size = 12, face = "bold"),
      axis.text.y = element_text(color = "#E66A57", face = "bold"),
      axis.title.y.right = element_text(color = "#50A192", size = 12, face = "bold"),
      axis.text.y.right = element_text(color = "#50A192", face = "bold"),
      axis.line.x = element_blank(),
      axis.line.y.right = element_blank(),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5)
    )
  plot.1.f
  #ggsave("04_images/h2_pv_feb_prod.png", plot = plot.1.f, width = 7.5, height = 4, dpi = 300)
}


# February - H2 PV price
{
  #Combined
  plot.2.f = ggplot(february, aes(x = Time, group = 1)) +
    geom_line(aes(y = `10 op`), color = "#E66A57", linewidth = 1) +
    geom_line(aes(y = coeff.2  * `power price`), color = "#4967AA", linewidth = 1) +
    
    scale_y_continuous(
      name = bquote(bold("Electrolyzer [MW]")),
      breaks = seq(0, 70, 10),
      sec.axis = sec_axis(
        trans = ~ (. - 0) / coeff.2, 
        name = bquote(bold("Power Price [€/MWh]")),
        breaks = seq(0,80, 10)
      )
    ) +
    scale_x_datetime(
      name = "Time",
      date_breaks = "1 day",
      date_labels = "%d/%m"
    ) +
    theme_bw() +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "#E66A57", size = 12, face = "bold"),
      axis.text.y = element_text(color = "#E66A57", face = "bold"),
      axis.title.y.right = element_text(color = "#4967AA", size = 12, face = "bold"),
      axis.text.y.right = element_text(color = "#4967AA", face = "bold"),
      axis.line.x = element_blank(),
      axis.line.y.right = element_blank(),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5)
    )
  plot.2.f
  #ggsave("04_images/h2_pv_feb_price.png", plot = plot.2.f, width = 7.5, height = 4, dpi = 300)
}


# April - H2 PV production
{
  #Combined
  plot.1.a = ggplot(april, aes(x = Time, group = 1)) +
    geom_line(aes(y = `10 op`), color = "#E66A57", linewidth = 1) +
    geom_line(aes(y = coeff.1  * `PV Production`), color = "#50A192", linewidth = 1) +
    
    scale_y_continuous(
      name = bquote(bold("Electrolyzer [MW]")),
      breaks = seq(0, 80, 10),
      sec.axis = sec_axis(
        trans = ~ . / coeff.1, 
        name = bquote(bold("PV [MW]")),
        breaks = seq(0,300, 50)
      )
    ) +
    scale_x_datetime(
      name = "Time",
      date_breaks = "1 day",
      date_labels = "%d/%m"
    ) +
    theme_bw() +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "#E66A57", size = 12, face = "bold"),
      axis.text.y = element_text(color = "#E66A57", face = "bold"),
      axis.title.y.right = element_text(color = "#50A192", size = 12, face = "bold"),
      axis.text.y.right = element_text(color = "#50A192", face = "bold"),
      axis.line.x = element_blank(),
      axis.line.y.right = element_blank(),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5)
    )
  plot.1.a
  #ggsave("04_images/h2_pv_april_prod.png", plot = plot.1.a, width = 7.5, height = 4, dpi = 300)
}


# April - H2 PV price
{
  #Combined
  plot.2.a = ggplot(april, aes(x = Time, group = 1)) +
    geom_line(aes(y = `10 op`), color = "#E66A57", linewidth = 1) +
    geom_line(aes(y = coeff.2  * `power price`), color = "#4967AA", linewidth = 1) +
    
    scale_y_continuous(
      name = bquote(bold("Electrolyzer [MW]")),
      breaks = seq(0, 70, 10),
      sec.axis = sec_axis(
        trans = ~ (. - 0) / coeff.2, 
        name = bquote(bold("Power Price [€/MWh]")),
        breaks = seq(0,80, 10)
      )
    ) +
    scale_x_datetime(
      name = "Time",
      date_breaks = "1 day",
      date_labels = "%d/%m"
    ) +
    theme_bw() +
    #theme_classic() +
    theme(
      axis.title.x = element_text(color = "black", size = 12, face = "bold"),
      axis.text.x = element_text(color = "black", face = "bold"),
      axis.title.y = element_text(color = "#E66A57", size = 12, face = "bold"),
      axis.text.y = element_text(color = "#E66A57", face = "bold"),
      axis.title.y.right = element_text(color = "#4967AA", size = 12, face = "bold"),
      axis.text.y.right = element_text(color = "#4967AA", face = "bold"),
      axis.line.x = element_blank(),
      axis.line.y.right = element_blank(),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5)
    )
  plot.2.a
  #ggsave("04_images/h2_pv_april_price.png", plot = plot.2.a, width = 7.5, height = 4, dpi = 300)
}
