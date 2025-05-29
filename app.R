# Here is the Shiny app where users can look at homes through a map and prices. 
# Forecats were made to estimate interest rates and house indices.
# A user can input their own information in Map page. The trend page can help encourage them as well as the forecasted estimate!

library(shiny)
library(leaflet)
library(plotly)
library(dplyr)

#  1) LOAD DATA ---
df_listings <- read.csv("SWFL_Data_Cleaned_Final_Version.csv", stringsAsFactors = FALSE) %>%
  rename_all(tolower)

collier <- read.csv("Collier_County_Price_Index.csv", stringsAsFactors = FALSE) %>%
  rename(date = observation_date, collier_hpi = ATNHPIUS12021A) %>%
  mutate(date = as.Date(date))

lee <- read.csv("Lee_County_Price_Index.csv", stringsAsFactors = FALSE) %>%
  rename(date = observation_date, lee_hpi = ATNHPIUS12071A) %>%
  mutate(date = as.Date(date))

hpi_df <- inner_join(collier, lee, by = "date")

med2024 <- hpi_df %>%
  filter(format(date, "%Y") == "2024") %>%
  summarize(collier = median(collier_hpi, na.rm = TRUE),
            lee     = median(lee_hpi,    na.rm = TRUE))

mortgage <- read.csv("MORTGAGE30US.csv", stringsAsFactors = FALSE) %>%
  rename(date = observation_date, mortgage_rate = MORTGAGE30US) %>%
  mutate(date = as.Date(date))

# Hard-coded next-month forecasts
next_fc     <- c(Collier = 397340, Lee = 343490)
mortgage_fc <- 6.76


# 2) UI ---
ui <- navbarPage("Home Buying Advisor",
                 
                 # === Map Tab ===
                 tabPanel("Map",
                          sidebarLayout(
                            sidebarPanel(
                              selectInput("county", "County", choices = c("Collier", "Lee")),
                              sliderInput("budget", "Price Range ($)",
                                          min   = min(df_listings$price, na.rm = TRUE),
                                          max   = max(df_listings$price, na.rm = TRUE),
                                          value = c(min(df_listings$price, na.rm = TRUE),
                                                    max(df_listings$price, na.rm = TRUE)),
                                          step  = 5000, pre = "$", sep = ","),
                              numericInput("beds",  "Min Beds",  value = 1, min = 0, max = 10),
                              numericInput("baths", "Min Baths", value = 1, min = 0, max = 10),
                              checkboxInput("gated","Gated Only", value = FALSE),
                              hr(),
                              numericInput("salary","Annual Salary ($)",     value = 60000, step = 1000),
                              numericInput("dp",    "Down Payment (%)",      value = 20,    min = 0, max = 100),
                              numericInput("mr",    "Mortgage Rate (%)",     value = mortgage_fc, min = 0, step = 0.01),
                              hr(),
                              verbatimTextOutput("medianPriceText"),
                              verbatimTextOutput("affordText")
                            ),
                            mainPanel(
                              leafletOutput("map", height = "600px")
                            )
                          )
                 ),
                 
                 # === Trends Tab ===
                 tabPanel("Trends",
                          fluidRow(
                            column(6, plotlyOutput("hpiPlot")),
                            column(6, plotlyOutput("mortgagePlot"))
                          ),
                          hr(),
                          verbatimTextOutput("forecastText")
                 )
                 
)


# 3) SERVER ---
server <- function(input, output, session) {
  
  # 3a) Filter by county (lat ≥26.3398 = Lee; else Collier)
  filtered <- reactive({
    df_listings %>%
      mutate(county = ifelse(latitude >= 26.3398, "Lee", "Collier")) %>%
      filter(county == input$county,
             price  >= input$budget[1],
             price  <= input$budget[2],
             beds   >= input$beds,
             baths  >= input$baths) %>%
      { if (input$gated) filter(., community_number == 1) else . }
  })
  
  # 3b) Median‐HPI text
  output$medianPriceText <- renderText({
    med <- if (input$county == "Collier") med2024$collier else med2024$lee
    paste0("2024 Median ", input$county, " HPI: ",
           formatC(round(med, 0), big.mark = ","))
  })
  
  # 3c) Affordability
  output$affordText <- renderText({
    monthly_budget <- input$salary * 0.25 / 12
    r <- input$mr / 100 / 12
    n <- 30 * 12
    principal_max <- monthly_budget * (1 - (1 + r)^(-n)) / r
    price_max     <- principal_max / (1 - input$dp/100)
    
    paste0(
      "Based on your inputs:\n",
      " • Max monthly payment (25% of salary): $", formatC(round(monthly_budget, 0), format="d", big.mark=","), "\n",
      " • Max mortgage principal: $",                formatC(round(principal_max,   0), format="d", big.mark=","), "\n",
      " • With ", input$dp, "% down → Max home price: $", formatC(round(price_max, 0), format="d", big.mark=",")
    )
  })
  
  # 3d) Leaflet map
  output$map <- renderLeaflet({
    df <- filtered()
    leaflet(df) %>% addTiles() %>%
      setView(lng = mean(df$longitude, na.rm=TRUE),
              lat = mean(df$latitude,  na.rm=TRUE),
              zoom = 11) %>%
      addCircleMarkers(
        lng = ~longitude, lat = ~latitude,
        radius = 6, color = "blue", stroke = FALSE, fillOpacity = 0.6,
        clusterOptions = markerClusterOptions(),
        popup = ~paste0(
          "<b>Address:</b> ", address, "<br>",
          "<b>Price:</b> $", formatC(price, big.mark=","), "<br>",
          "<b>Beds/Baths:</b> ", beds, "/", baths, "<br>",
          "<b>Gated:</b> ",
          ifelse(!is.na(community_number) & community_number == 1, "Yes",
                 ifelse(!is.na(community_number), "No", "Missing Info")
          ), "<br>",
          "<b>Zip:</b> ", zipcode
        )
      )
  })
  
  # 3e) HPI time‐series
  output$hpiPlot <- renderPlotly({
    plot_ly(hpi_df, x = ~date) %>%
      add_lines(y = ~collier_hpi, name = "Collier HPI") %>%
      add_lines(y = ~lee_hpi,     name = "Lee HPI") %>%
      layout(title = "House Price Index",
             xaxis = list(title = "Date"),
             yaxis = list(title = "HPI"))
  })
  
  # 3f) Mortgage rate time‐series
  output$mortgagePlot <- renderPlotly({
    plot_ly(mortgage, x = ~date, y = ~mortgage_rate,
            type = "scatter", mode = "lines") %>%
      layout(title = "30-Year Fixed Mortgage Rate",
             xaxis = list(title = "Date"),
             yaxis = list(title = "Rate (%)"))
  })
  
  # 3g) Forecast text
  output$forecastText <- renderPrint({
    cat(
      "1-Month Ahead Forecasts for Best Methods:\n\n",
      sprintf("Collier  via Drift  → forecast = %s", format(next_fc["Collier"], big.mark=",")), "\n",
      sprintf("Lee      via SARIMA → forecast = %s", format(next_fc["Lee"],     big.mark=",")), "\n",
      sprintf("Mortgage via HWMul  → forecast = %.2f", mortgage_fc), "\n",
      sep = ""
    )
  })
  
} # end server


# 4) RUN APP ---
shinyApp(ui, server)
