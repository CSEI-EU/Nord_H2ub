cat("\014")
rm(list = ls())
graphics.off()

setwd("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects")

### Libraries
library(readr)
library(dplyr)
library(stringr)
library(openxlsx)
library(purrr)
library(lubridate)
library(ggplot2)


######################
###  IMPORT DATA   ###
######################

data <- read.xlsx("01_input_data/02_input_prepared/other.xlsx")


######################
###   DATA PREP    ###
######################
segment_data <- data.frame(
  x_start = c(0.130774, 0.227354667, 0.323935333, 0.420516, 0.517096667, 
              0.613677333, 0.710258, 0.806838667, 0.903419333),
  x_end = c(0.227354667, 0.323935333, 0.420516, 0.517096667, 
            0.613677333, 0.710258, 0.806838667, 0.903419333, 1),
  y_value = c(0.792753619, 0.789015771, 0.761699218, 0.730892763, 0.707576202,
              0.685952362, 0.665717205, 0.645394376, 0.633771173)
)

# Plotting the data
eff_plot <- ggplot(data, aes(x = `Power.[%]`)) +
  geom_segment(data = segment_data, aes(x = x_start, xend = x_end, y = y_value, yend = y_value, color = "Adjusted efficiency"), size = 1.2) +
  geom_smooth(aes(y = `Efficiency_scaled.[%]`, color = "Variable efficiency"), method = "gam", size = 1.2, se = FALSE) +
  geom_segment(aes(x = 0.13, xend = max(data$`Power.[%]`), y = 0.75, yend = 0.75, color = "Constant efficiency"), linetype = 'solid', size = 1) +
  scale_color_manual(
    name = "Legend",
    values = c("Adjusted efficiency" = '#242e70', "Variable efficiency" = '#50a092', "Constant efficiency" = '#ffc000'),
    limits = c("Constant efficiency", "Variable efficiency", "Adjusted efficiency") 
  ) +
  labs(x = 'Power [%]', y = 'Adjusted Efficiency') +
  xlim(0, NA) +
  theme_minimal() +
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.border = element_blank(),
    legend.position = "bottom"
  )

ggsave("03_output_data/02_runs_EURO/03_plots/efficiency.png", plot = eff_plot, width = 5.47, height = 4.38, units = "in", bg = "transparent")

