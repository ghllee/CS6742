setwd("/home/jhessel/Desktop/NLP/git/AltruisticLanguage")
myData <- read.csv("success.csv")
install.packages("penalized")
library(penalized)
penalized(response = myData$success,
          penalized = myData[,-match("success", colnames(myData))],
          lambda2=1.0, model = "logistic")