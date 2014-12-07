setwd("/home/jhessel/Desktop/NLP/git/AltruisticLanguage")
library('Matrix')
library('glmnet')
library('foreach')
library('doParallel')

topK <- 50
rsort <- function(x) {
  sort(x, decreasing = TRUE)
}
myResult <- read.csv("altBinaryTarget.csv", header = F)$V1
myDataControl <- readMM("controlsWithSucc.mtx")
myData <- readMM("allWithSucc.mtx")

#NORMALS
crossValid <- cv.glmnet(myData,
                        myResult, type.measure = 'class',
                        family="binomial", alpha=1, parallel=T)
bestlambda<-crossValid$lambda.min
mse.min <- crossValid$cvm[crossValid$lambda == bestlambda]
myCoefs <- coef(crossValid, s=bestlambda)
myCoefMatrix <- as.matrix(myCoefs)
myPredictions <- predict(crossValid, myData, type = "class", s=bestlambda)
colnames(myCoefMatrix) <- c("Beta")
headers <- read.csv("allHeadersWithSucc.csv")
rownames(myCoefMatrix) <- c("Intercept", colnames(headers))

apply(myCoefMatrix, 2, sort)[1:topK,]
apply(myCoefMatrix, 2, rsort)[1:topK,]

#Just Controls
crossValidControl <- cv.glmnet(myDataControl,
                               myResult, type.measure = 'class',
                               family="binomial", alpha=1, parallel=T)
bestlambdaControl <-crossValidControl$lambda.min
mse.minControl <- crossValidControl$cvm[crossValidControl$lambda == bestlambdaControl]
myCoefsControl <- coef(crossValidControl, s=bestlambdaControl)
myCoefMatrixControl <- as.matrix(myCoefsControl)
myPredictionsControl <- predict(crossValidControl, myDataControl,
                                type = "class", s=bestlambdaControl)
colnames(myCoefMatrixControl) <- c("Beta")
headersControl <- read.csv("controlHeadersWithSucc.csv")
rownames(myCoefMatrixControl) <- c("Intercept", colnames(headersControl))

apply(myCoefMatrixControl, 2, sort)[1:topK,]
apply(myCoefMatrixControl, 2, rsort)[1:topK,]


dev1 <- deviance(crossValid$glmnet.fit)[crossValid$lambda == bestlambda]
dev2 <- deviance(crossValidControl$glmnet.fit)[crossValidControl$lambda == bestlambdaControl]
df1 <- crossValid$glmnet.fit$df[crossValid$lambda == bestlambda]
df2 <- crossValidControl$glmnet.fit$df[crossValidControl$lambda == bestlambdaControl]
1-pchisq(dev2-dev1, df1-df2)
