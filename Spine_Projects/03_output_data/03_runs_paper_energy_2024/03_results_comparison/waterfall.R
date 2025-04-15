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
  library(waterfalls)
}


#Import data
{
  data_flows = as.data.frame(read_excel("02_output_prepared/review_1/output_base_10op_run.xlsx", sheet = "flows_node_states"))
  data_lcoe = as.data.frame(read_excel("02_output_prepared/review_1/output_base_10op_run.xlsx", sheet = "LCOE"))
  data_inv = as.data.frame(read_excel("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/01_input_data/01_input_raw/investment_cost_overview/investment_cost_overview.xlsx"))
  data_energy = as.data.frame(read_excel("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects/01_input_data/01_input_raw/energy_prices/2019-2050.xlsx"))
}

energy_production = data_lcoe$`energy_production [t]`[1] 
energy_production_anf = 9.81814740744929 * data_lcoe$`energy_production [t]`[1]


# Calculate investment blocks
inv_costs_pv = (304 * data_inv$`Investment_Cost [Euro/MW or MWh] Value 2020`[1]) / energy_production_anf
inv_costs_elec = (as.numeric(data_flows$units_invested.3_electrolyzer__realization[4]) * 52 * data_inv$`Investment_Cost [Euro/MW or MWh] Value 2020`[3]) / energy_production_anf
inv_costs_methanol = (as.numeric(data_flows$units_invested.2_dist_tower__realization[4]) * 52 * data_inv$`Investment_Cost [Euro/MW or MWh] Value 2020`[12]) / energy_production_anf
inv_costs_total = (data_lcoe$`total_investment`[1]) / energy_production_anf
#inv_costs_storage = as.numeric(data_flows$objective_storage_investment_costs_Model__[4]) * 0.571447592 / energy_production_anf
inv_costs_storage = 334376.152584158 / energy_production_anf
inv_costs_rest = inv_costs_total - inv_costs_pv - inv_costs_elec - inv_costs_methanol - inv_costs_storage


# Calculate other "variable costs"
costs_power = sum(as.numeric(data_flows$connection_flow.14_pl_wholesale_to_node_power[4:nrow(data_flows)]) * data_energy$`2019`) / energy_production
costs_grid = sum(as.numeric(data_flows$connection_flow.14_pl_wholesale_to_node_power[4:nrow(data_flows)])) * 11.70241287 / energy_production
costs_co2 = sum(as.numeric(data_flows$unit_flow.4_co2_vaporizer_from_node_co2[4:nrow(data_flows)])) * 26.81 / energy_production
costs_water = sum(as.numeric(data_flows$unit_flow.11_electrolyzer_from_node_water[4:nrow(data_flows)]) + as.numeric(data_flows$unit_flow.16_steam_plant_from_node_water[4:nrow(data_flows)])) * 0.0015 / energy_production


# Calculate revenue blocks
rev_dh = - sum(as.numeric(data_flows$connection_flow.7_pl_dh_to_node_dh[4:nrow(data_flows)])) * 18.579 / energy_production
rev_pv = - (data_lcoe$`LCOE [Euro/t]`[1] - data_lcoe$`LCOE [Euro/t]`[2])


# Rest is other (fom)
costs_fom = data_lcoe$`LCOE [Euro/t]`[1] - inv_costs_total - rev_dh - costs_power - costs_grid - costs_water - costs_co2


# Create one single database
names = c("PV", "Electrolyser", "Methanol", "Other Units", "Storage",
          "Power", "Grid", "CO2 + Water", "Other",
          "DH", "Power Market", "LCOM")
values_short = c(inv_costs_pv, inv_costs_elec, inv_costs_methanol, inv_costs_rest, inv_costs_storage,
           costs_power, costs_grid, costs_co2 + costs_water, costs_fom,
           rev_dh, rev_pv)
total = - sum(values_short)
category = c("Investment Costs", "Investment Costs", "Investment Costs", "Investment Costs", "Investment Costs", 
             "Variable Costs", "Variable Costs", "Variable Costs", "Variable Costs", 
             "Revenue", "Revenue", "LCOM")

df = data.frame(x = factor(names, levels = names), values = round(c(values_short, total)), category = category)

df$category <- factor(df$category, levels = c("Investment Costs", "Variable Costs", "Revenue", "LCOM"))

for (i in 1:(nrow(df)-1)) {
  
  value = sum(df$values[1:i])
  
  if (df$values[i] < 0) {
    value_new = value - 60
  } else {
    value_new = value + 60
  }
  
  df$test[i] = value
  df$former[i] = value_new
}

df$before[1] = 0
for (i in 2:(nrow(df))) {
  df$before[i] = df$test[i-1]-2
}
df$former[nrow(df)] = -df$values[nrow(df)] + 60
df$test[nrow(df)] = sum(df$values[1:nrow(df)])

col <- ifelse (df$category == "Investment Costs", "#4967AA", 
               ifelse(df$category == "Variable Costs", "#6793D6", 
                      ifelse(df$category == "Revenue", "#50A192", "grey")))

#Graph
{
  # Create waterfall diagram
  p = waterfall(df, 
                calc_total = FALSE, 
                linetype = 1,
                rect_text_labels = rep("", nrow(df)),
                fill_by_sign = FALSE, 
                fill_colours = col, 
                rect_border = col) +
    
    # Add y axis label
    scale_y_continuous(
      name = bquote(bold("[€/t CH"[3]*"OH]")),
      breaks = seq(0, 1600, 500)
    ) +
    
    # Add top and right axis
    coord_cartesian(xlim = c(NA, 13), ylim=c(-50, 1650), expand=FALSE, clip="off") +
    annotate("segment", x = 0, xend = 13, 
             y=1650, yend = 1650, color="black", linewidth =0.5) + #upper axis
    annotate("segment", x = 13, xend = 13, 
             y=-50, yend = 1650, color="black", linewidth =0.5) + #upper axis
    
    # Dummy layer to trigger legend
    geom_point(data = df, 
               aes(x = x, y = 0, fill = category), 
               shape = 22, size = 5, alpha = 0) +
    
    scale_fill_manual(values=c("Investment Costs" = "#4967AA", 
                               "Variable Costs" = "#6793D6", 
                               "Revenue" = "#50A192", 
                               "LCOM" = "grey")) +
    
    scale_color_manual(values = c("Investment Costs" = "#4967AA",
                                  "Variable Costs" = "#6793D6",
                                  "Revenue" = "#50A192",
                                  "LCOM" = "grey"
                                  )) +
    geom_text(data = df,
              aes(x = x, y = former, 
                  label = round(c(values_short, -total)), colour = category
              ),
              size = 3, fontface ="bold") + 
    
    # Force legend appearance for fill
    guides(fill = guide_legend(override.aes = list(shape = 16, size = 4))) +
    
    theme_classic() +
    theme(
      axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1, color = "black", face = "bold"),
      axis.text.y = element_text(color = "black", face = "bold"),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
      axis.title.x = element_blank(),
      legend.title = element_blank(),
      legend.text = element_text(color = "black", face="bold")
    )
  p
  #ggsave("04_images/waterfall.png", plot = p, width = 7.5, height = 4, dpi = 300)
}


#Graph
{
  # Create waterfall diagram
  plot = ggplot(df, aes(x = x, group = 1)) +
    
    # Plot only the range as segments starting from Low_emission
    geom_segment(aes(x = as.numeric(x), 
                     xend = as.numeric(x), 
                     y = `before`, 
                     yend = `test`,
                     color = `category`), 
                 #color = col,
                 size = 7) +
    
    # Add black line at 0
    annotate("segment", x = 0, xend = 12.89, 
             y=0, yend = 0, color="black", linewidth =0.25) + 
    
    scale_y_continuous(
      name = bquote(bold("[€/t CO"[2]*"]")),
      breaks = seq(0, 1500, 500)
    ) +
    
    scale_x_discrete(
      name = "",
    ) +
    
    scale_color_manual(values=c("Investment Costs" = "#4967AA", 
                               "Variable Costs" = "#6793D6", 
                               "Revenue" = "#50A192", 
                               "LCOM" = "grey")) +
    geom_text(data = df,
              aes(x = x, y = former, 
                  label = round(c(values_short, -total)), colour = category
              ),
              size = 3.5, fontface ="bold") +
    theme_bw() +
    theme(
      axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1, color = "black", size = 10, face = "bold"),
      axis.title.y = element_text(color = "black", size = 12, face = "bold"),
      axis.text.y = element_text(color = "black", size = 10, face = "bold"),
      panel.grid.major = element_line(color = "gray98", linewidth = 0.5),
      panel.grid.minor = element_line(color = "gray98", linewidth = 0.5),
      #legend.position = c(0.09, 0.9),
      #legend.background = element_rect(fill='transparent'),
      legend.text = element_text(size = 10),
      legend.title = element_blank(),
      legend.direction = "vertical",
      axis.ticks.y.right = element_blank(),
      axis.text.y.right = element_blank()
    )
  plot
  #ggsave("04_images/waterfall.png", plot = p, width = 7.5, height = 4, dpi = 300)
}

