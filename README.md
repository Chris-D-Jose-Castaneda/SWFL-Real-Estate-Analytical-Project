# 🏡 SWFL Real Estate Home Buying Advisor (SWFL) 🏖️

Welcome to the Home Buying Advisor project—a comprehensive analytics suite built to help prospective buyers navigate the complex housing markets of Southwest Florida. By combining automated data collection, rigorous statistical modeling, and an interactive R Shiny dashboard, this tool delivers timely insights into property prices, market trends, and affordability metrics.

🎯 Project Scope

This repository covers the end-to-end workflow for generating actionable real estate insights. We begin with scraping detailed property listings from Realtor.com, followed by precise geocoding of addresses. I create an ETL pipeline then cleann and wrangle the raw data by looking at important features, while integrating economic indicators including county house price indices and mortgage rates. Advanced statistical and machine learning models quantify price drivers and produce short-term forecasts. Finally, an R Shiny application presents interactive maps, trend charts, and affordability calculators to guide homebuyers in a changing market. Remember to have all packages installed prior to running

📁 File Descriptions

updated_mls_scraper.py - Implements a robust Selenium-based scraper that collects listing details—price, beds, baths, square footage, and more—from Realtor.com. It writes the raw output to april13_listings_raw_listings.csv for further processing.

Zipcode.py - Normalizes and geocodes property addresses using Geopy’s Nominatim service, with a U.S. Census API fallback. The script enriches each listing with precise latitude and longitude, saving results to Final_SWFL_With_Fallback_Coords.csv.

Data Cleaning.ipynb - Executes the ETL pipeline: it ingests raw CSV files, sanitizes and parses text fields, engineers derived variables (e.g., ppsf, age), handles outliers, and merges economic data. The cleaned dataset is exported as SWFL_Data_Cleaned_Final_Version.csv.

Economic_Parameters.ipynb - Retrieves and processes macroeconomic time series—including 30-year fixed mortgage rates (MORTGAGE30US.csv), SPY, DJIA, and county HPIs (Collier_County_Price_Index.csv, Lee_County_Price_Index.csv)—and visualizes their historical trends.

Modeling.ipynb - Explores predictive modeling approaches: OLS regression with interaction terms, regularized regressions (Ridge/Lasso), ARIMA forecasting, and machine learning (Random Forest, XGBoost). It benchmarks models using metrics like R² and RMSE and generates                          diagnostic plots.

app.R - A R Shiny application that loads cleaned data and economic series to provide an interactive dashboard with map-based listings visualization, historical trend charts, forecast results, and an affordability calculator for users to simulate different scenarios.

Raw_SWFL_Data.csv - Contains the initial, unprocessed data directly exported from the scraper, including all original listing fields for transparency and debugging.

Final_SWFL_With_Fallback_Coords.csv - Intermediate output showing the dataset after geocoding, complete with latitude and longitude values for each listing. This is the output file after running the python file w/ Zipcodes. 

SWFL_Data_Cleaned_Final_Version.csv - The final, cleaned, and feature-engineered dataset used for all analyses and visualizations. It includes merged economic variables, outlier treatment, and derived metrics.

🌟 Cont'd

Please feel free to use this repository for a data science or quantitative research projects. Don't forget to ⭐ this repository :)

- Chris



