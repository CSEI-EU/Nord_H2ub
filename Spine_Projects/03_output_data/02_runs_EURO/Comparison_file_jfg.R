cat("\014")
rm(list = ls())
graphics.off()

setwd("C:/Users/djh.eco/OneDrive - CBS - Copenhagen Business School/Documents/GitHub/Nord_H2ub/Spine_Projects")
#setwd("C:/Users/jfg.eco/Documents/GitHub/Nord_H2ub/Spine_Projects")

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

base_case <- read.xlsx("03_output_data/02_runs_EURO/01_output_raw/Output_exported_base_case.xlsx")
other_case <- read.xlsx("03_output_data/02_runs_EURO/01_output_raw/Output_exported_constant_efficiency.xlsx")

power_price <- read.xlsx("01_input_data/01_input_raw/Day_ahead_prices_2019.xlsx")

##################################
###  FUNCTION TO PREPARE DATA  ###
##################################

prepare_data <- function(data, power_price) {
  ### Calculate electricity flows
  colnames(data) <- make.unique(colnames(data))
  column_names <- colnames(data)
  unit_flow_columns <- grep("^unit_flow\\.\\d+$", column_names, value = TRUE)
  power_kasso_columns <- sapply(unit_flow_columns, function(col) {
    data[3, col] == "Power_Kasso"
  })
  selected_columns <- unit_flow_columns[power_kasso_columns]
  
  data_subset <- data[4:nrow(data), ]
  data_subset[, selected_columns] <- lapply(data_subset[, selected_columns, drop = FALSE], as.numeric)
  summed_data <- rowSums(data_subset[, selected_columns, drop = FALSE], na.rm = TRUE)
  
  identifier <- data_subset[, 1, drop = FALSE]
  result <- cbind(identifier, Summed_Power_Flow = summed_data)
  
  ### Add danish power prices to table
  power_price_dk <- power_price %>%
    filter(PriceArea == "DK1")
  result$Power_Price <- power_price_dk$SpotPriceEUR
  result$Total_power_costs <- result$Summed_Power_Flow * result$Power_Price
  
  ### Add units produced and storages
  end_products_filter <- sapply(unit_flow_columns, function(col) {
    data[2, col] == "to_node" &&
      data[3, col] == "Hydrogen_Kasso" || data[3, col] == "E-Methanol_Kasso" 
  })
  end_products_columns <- unit_flow_columns[end_products_filter]
  storage_state_columns <- grep("^node_state", column_names, value = TRUE)
  
  columns_comb <- union(end_products_columns, storage_state_columns)
  data_subset[, columns_comb] <- lapply(data_subset[, columns_comb, drop = FALSE], as.numeric)
  col_names_to_assign <- data[3, columns_comb]
  
  for (col in columns_comb) {
    result[[col]] <- data_subset[, col]
  }
  num_cols_to_rename <- length(columns_comb)
  start_index <- ncol(result) - num_cols_to_rename + 1
  end_index <- ncol(result)
  names(result)[start_index:end_index] <- col_names_to_assign
  
  colnames(result) <- make.unique(colnames(result))
  
  # specify date format
  result$X1 <- as.POSIXct(result$X1, format="%Y-%m-%dT%H:%M:%S")
  
  return(result)
}

######################
###   DATA PREP    ###
######################

result_base <- prepare_data(base_case, power_price)
result_other <- prepare_data(other_case, power_price)

######################
###   COMPARISON   ###
######################

# Hydrogen production
mean_hydrogen_base = mean(result_base$Hydrogen_Kasso)
mean_hydrogen_other = mean(result_other$Hydrogen_Kasso)
# evidently more hydrogen needs to be produced in the constant case -> loss in storage
means_df <- data.frame(
  Source = c("Base", "Other"),
  Mean_Hydrogen_Production = c(mean_hydrogen_base, mean_hydrogen_other)
)
max_mean <- max(means_df$Mean_Hydrogen_Production)
ggplot(means_df, aes(x = Source, y = Mean_Hydrogen_Production, fill = Source)) +
  geom_bar(stat = "identity", width = 0.4) +
  scale_fill_manual(values = c("Base" = "#4C72B0", "Other" = "#55A868")) +
  labs(title = "Mean Hydrogen Production",
       x = "",
       y = "Mean Hydrogen Production") +
  ylim(0, max_mean * 1.2) +
  theme_minimal()
# effect is slight, not sure it is really visible in graph, might be better to show in numbers


### Plots
df_comb <- data.frame(time = result_base$X1, 
                      base_energy_costs = result_base$Total_power_costs, 
                      other_energy_costs = result_other$Total_power_costs,
                      hydrogen_base = result_base$Hydrogen_Kasso,
                      hydrogen_other = result_other$Hydrogen_Kasso,
                      hydrogen_storage_base = result_base$realisation,
                      hydrogen_storage_other = result_other$realisation)
start_date <- as.POSIXct("2019-01-01")
end_date <- start_date + days(7)

df_comb_first_week <- df_comb %>% filter(time >= start_date & time < end_date)

# Power costs
ggplot(data = df_comb_first_week, aes(x = time)) +
  geom_line(aes(y = base_energy_costs, color = "Base"), linewidth = 0.75) +
  geom_line(aes(y = other_energy_costs, color = "Other"), linewidth = 0.75) +
  labs(title = "Power Costs per Hour in First Week",
       x = "Time",
       y = "Value",
       color = "Legend") +
  theme_minimal()

# Hydrogen production
hydro_plot <- ggplot(data = df_comb_first_week, aes(x = time)) +
  geom_line(aes(y = hydrogen_base, color = "Variable efficiency"), linewidth = 0.9) +
  geom_line(aes(y = hydrogen_other, color = "Constant efficiency"), linewidth = 0.9) +
  scale_color_manual(
    name = "Legend",
    values = c("Variable efficiency" = "#8FA3CF", "Constant efficiency" = "#242E70"),
    limits = c("Variable efficiency", "Constant efficiency") 
  ) +
  labs(x = "Time", y = "Hydrogen production", color = "Legend") +
  theme_minimal() +
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.border = element_blank(),
    legend.position = "bottom"
  )

ggsave("03_output_data/02_runs_EURO/03_plots/hydro_production.png", plot = hydro_plot, width = 5.48, height = 4.84, units = "in", bg = "transparent")

# Storage level
ggplot(data = df_comb_first_week, aes(x = time)) +
  geom_line(aes(y = hydrogen_storage_base, color = "Variable efficiency"), linewidth = 0.9) +
  geom_line(aes(y = hydrogen_storage_other, color = "Constant efficiency"), linewidth = 0.75) +
  scale_color_manual(values = c("Variable efficiency" = "#ffc000", "Constant efficiency" = "#242E70")) +
  labs(title = "Hydrogen Storage Level in First Week",
       x = "Time",
       y = "Value",
       color = "Legend") +
  theme_minimal()

# Production vs. Costs
production_var <- sum(result_base$Hydrogen_Kasso)
production_con <- sum(result_other$Hydrogen_Kasso)
costs_var <- sum(result_base$Total_power_costs)
costs_con <- sum(result_other$Total_power_costs)

methods <- rep(c("Hydrogen Production [MWh]", "Production Cost [Euro]"), each = 2)
method_type <- rep(c("Variable efficiency", "Constant efficiency"), 2)
values <- c(production_var, production_con, costs_var, costs_con)

data <- data.frame(
  Metric = methods,
  Method = method_type,
  Value = values
)

colors <- c("Variable efficiency" = "#8FA3CF", "Constant efficiency" = "#242E70")

ggplot(data, aes(x = Metric, y = Value, fill = Method)) +
  geom_bar(stat = "identity", position = position_dodge()) +
  scale_fill_manual(values = colors) +
  labs(x = "Metric",
       y = "Value",
       fill = "Legend") +
  scale_y_continuous(
    name = "Hydrogen Production [MWh]",
    sec.axis = sec_axis(~ ., name = "Power Cost [Euro]", labels = scales::comma),
    expand = c(0, 20000000),
    limits = c(250000, 25000000)  # Adjusted limits for better visibility
  ) +
  theme_minimal() +
  scale_y_continuous(
    sec.axis = sec_axis(~ ., name = "Cost [Euro]", labels = scales::comma)
  ) +
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.border = element_blank(),
    legend.position = "bottom"
  )
