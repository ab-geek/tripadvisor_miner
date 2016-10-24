from tripadvisor import TripAdvisor
tripadvisorObj = TripAdvisor()
tripadvisorObj.scrape("dallas",'en')
tripadvisorObj.scrape("Bohol Island",'zh-Hant')
tripadvisorObj.scrape("Bohol Island",'zh-Hans')
# tripadvisorObj.scrape("dallas",'fr')
# tripadvisorObj.scrape("dallas",'en-CA')