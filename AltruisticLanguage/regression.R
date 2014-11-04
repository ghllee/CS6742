setwd("/home/jhessel/Desktop/NLP/git/AltruisticLanguage")
library('Matrix')
library('glmnet')
myData <- readMM("data.mtx")
myResult <- factor(read.csv("result.csv", header = F)$V1)
crossValid <- cv.glmnet(myData, myResult, family="binomial", alpha=1)
bestlambda<-crossValid$lambda.min
myCoefs <- coef(crossValid, s=bestlambda)
myPredictions <- predict(crossValid, myData, type = "class", s=bestlambda)
