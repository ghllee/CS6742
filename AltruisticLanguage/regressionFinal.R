setwd("/home/jack/Desktop/NLP/CS6742/AltruisticLanguage")
library('Matrix')
library('glmnet')
library('foreach')
library('doParallel')
registerDoParallel()
rsort <- function(x) {
  sort(x, decreasing = TRUE)
}
setwd("regressionData")
dataSW <- readMM("all90Filter.mtx")
headersSW <- read.csv("allHeaders90Filter.csv")
dataNoSW <- readMM("all90FilternoSW.mtx")
headersNoSW <- read.csv("allHeaders90FilternoSW.csv")
dataControl <- readMM("allControls.mtx")
headersControl <- read.csv("allControlHeaders.csv")
setwd("..")

colnames(dataSW) <- colnames(headersSW)
colnames(dataNoSW) <- colnames(headersNoSW)
colnames(dataControl) <- colnames(headersControl)

dataControlTest2 <- dataControl[which(dataControl[,c("numBackers")]>=20),]
target2 <- dataControl[which(dataControl[,c("numBackers")]>=20),c("numBackers", "numAltruistic")]
target2 <- target2[,2]/target2[,1]

target <- dataControl[,c("numBackers", "numAltruistic")]
target <- target[,2]/target[,1]
target[is.nan(target)] <- 0
target <- target > .1

control <- cv.glmnet(dataControl[,-which(colnames(dataControl) %in% c("numBackers","numAltruistic", "Osuccess"))], target,
              family = "binomial",
              type.measure = "class",
              alpha = 1, parallel = T)

noSW <- cv.glmnet(dataNoSW[,-which(colnames(dataNoSW) %in% c("numBackers","numAltruistic", "Osuccess"))], target,
                family = "binomial",
                type.measure = "class",
                alpha = 1, parallel = T)

SW <- cv.glmnet(dataSW[,-which(colnames(dataSW) %in% c("numBackers","numAltruistic", "Osuccess"))], target,
                family = "binomial",
                type.measure = "class",
                alpha = 1, parallel = T)

test2 <- cv.glmnet(dataControlTest2[,-which(colnames(dataControlTest2) %in% c("numAltruistic"))], target2, family='gaussian', alpha=1, parallel = T)

holdoutNoSW <- cv.glmnet(dataNoSW[1:40000,-which(colnames(dataNoSW) %in% c("numBackers","numAltruistic", "Osuccess"))],
                       target[1:40000], family = "binomial", type.measure = "class", alpha = 1, parallel = T)

holdoutSW <- cv.glmnet(dataSW[1:40000,-which(colnames(dataSW) %in% c("numBackers","numAltruistic", "Osuccess"))],
                       target[1:40000], family = "binomial", type.measure = "class", alpha = 1, parallel = T)

holdoutControl <- cv.glmnet(dataControl[1:40000,-which(colnames(dataControl) %in% c("numBackers","numAltruistic", "Osuccess"))],
                            target[1:40000], family = "binomial", type.measure = "class", alpha = 1, parallel = T)


print("No SW Holdout Accuracy")
sum(predict(holdoutNoSW,
            dataNoSW[40001:nrow(dataNoSW),-which(colnames(dataNoSW) %in% c("numBackers","numAltruistic", "Osuccess"))],
            type='class')
    == target[40001:nrow(dataNoSW)])/(length(target[40001:nrow(dataNoSW)]))

print("SW Holdout Accuracy")
sum(predict(holdoutSW,
            dataSW[40001:nrow(dataSW),-which(colnames(dataSW) %in% c("numBackers","numAltruistic", "Osuccess"))],
            type='class')
    == target[40001:nrow(dataSW)])/(length(target[40001:nrow(dataSW)]))

print("Control Holdout Accuracy")
sum(predict(holdoutControl,
            dataControl[40001:nrow(dataControl),-which(colnames(dataControl) %in% c("numBackers","numAltruistic", "Osuccess"))],
            type='class')
            == target[40001:nrow(dataControl)])/(length(target[40001:nrow(dataControl)]))


topBottomK <- function(cvReg, k) {
  bestlambda<-cvReg$lambda.min
  mse.min <- cvReg$cvm[cvReg$lambda == bestlambda]
  print(1-mse.min)
  myCoefs <- coef(cvReg, s=bestlambda)
  myCoefMatrix <- as.matrix(myCoefs)
  print("BOTTOM")
  print(apply(myCoefMatrix, 2, sort)[1:k,])
  print("TOP")
  print(apply(myCoefMatrix, 2, rsort)[1:k,])
}

orderedCoefs <- function(cvReg) {
  bestlambda<-cvReg$lambda.min
  mse.min <- cvReg$cvm[cvReg$lambda == bestlambda]
  print(1-mse.min)
  myCoefs <- coef(cvReg, s=bestlambda)
  myCoefMatrix <- as.matrix(myCoefs)
  return(apply(myCoefMatrix, 2, sort))
}

topK <- 50
topBottomK(control, topK)
topBottomK(noSW, topK)
topBottomK(SW, topK)
topBottomK(test2, topK)
write.table(orderedCoefs(SW), file = "testFile.csv")