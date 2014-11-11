setwd("/home/jhessel/Desktop/NLP/git/AltruisticLanguage")
library('Matrix')
library('glmnet')
library('foreach')
library('doParallel')

topK <- 50
rsort <- function(x) {
  sort(x, decreasing = TRUE)
}
myResult <- factor(read.csv("target.csv", header = F)$V1)

#NORMALS
myData <- readMM("data.mtx")
crossValid <- cv.glmnet(myData, myResult, family="binomial",
                        alpha=1, type.measure = "class",
                        parallel=T, lambda = exp(seq(-10,-2, by=1)))
bestlambda<-crossValid$lambda.min
mse.min <- crossValid$cvm[crossValid$lambda == bestlambda]
myCoefs <- coef(crossValid, s=bestlambda)
myCoefMatrix <- as.matrix(myCoefs)
myPredictions <- predict(crossValid, myData, type = "class", s=bestlambda)
colnames(myCoefMatrix) <- c("Beta")
headers <- read.csv("headers.csv")
rownames(myCoefMatrix) <- c("Intercept", colnames(headers))

apply(myCoefMatrix, 2, sort)[1:topK,]
apply(myCoefMatrix, 2, rsort)[1:topK,]

#Just Controls
myDataControl <- readMM("dataControl.mtx")
crossValidControl <- cv.glmnet(myDataControl, myResult,
                               family="binomial", alpha=1, parallel=T,
                               type.measure = "class")
bestlambdaControl <-crossValidControl$lambda.min
mse.minControl <- crossValidControl$cvm[crossValidControl$lambda == bestlambdaControl]
myCoefsControl <- coef(crossValidControl, s=bestlambdaControl)
myCoefMatrixControl <- as.matrix(myCoefsControl)
myPredictionsControl <- predict(crossValidControl, myDataControl,
                                type = "class", s=bestlambdaControl)
colnames(myCoefMatrixControl) <- c("Beta")
headersControl <- read.csv("headersControl.csv")
rownames(myCoefMatrixControl) <- c("Intercept", colnames(headersControl))

apply(myCoefMatrixControl, 2, sort)[1:topK,]
apply(myCoefMatrixControl, 2, rsort)[1:topK,]

#Just Rewards
myDataRewards <- readMM("justRewards.mtx")
crossValidRewards <- cv.glmnet(myDataRewards, myResult,
                               family="binomial", alpha=1, parallel=T,
                               type.measure = "class", lambda = 10^seq(-15,-4, by=1))
bestlambdaRewards <-crossValidRewards$lambda.min
mse.minRewards <- crossValidRewards$cvm[crossValidRewards$lambda == bestlambdaRewards]
myCoefsRewards <- coef(crossValidRewards, s=bestlambdaRewards)
myCoefMatrixRewards <- as.matrix(myCoefsRewards)
myPredictionsRewards <- predict(crossValidRewards, myDataRewards,
                                type = "class", s=bestlambdaRewards)
colnames(myCoefMatrixRewards) <- c("Beta")
headersRewards <- read.csv("justRewards.csv")
rownames(myCoefMatrixRewards) <- c("Intercept", colnames(headersRewards))

apply(myCoefMatrixRewards, 2, sort)[1:topK,]
apply(myCoefMatrixRewards, 2, rsort)[1:topK,]
