setwd("/home/jack/Desktop/NLP/CS6742/AltruisticLanguage")
library('Matrix')
library('glmnet')
library('foreach')
library('doParallel')
registerDoParallel()

topK <- 50
rsort <- function(x) {
  sort(x, decreasing = TRUE)
}

data <- readMM("all90Filter.mtx")
headers <- read.csv("allHeaders90Filter.csv")
dataControl <- readMM("allControls.mtx")
headersControl <- read.csv("allControlHeaders.csv")
colnames(data) <- colnames(headers)
colnames(dataControl) <- colnames(headersControl)

target <- dataControl[,c("numBackers", "numAltruistic")]
target <- target[,2]/target[,1]
target[is.nan(target)] <- 0
target <- target > .1

control <- cv.glmnet(dataControl[,-which(colnames(dataControl) %in% c("numBackers","numAltruistic", "Osuccess"))], target,
              family = "binomial",
              type.measure = "class",
              alpha = 1, parallel = T)

all <- cv.glmnet(data[,-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))], target,
                family = "binomial",
                type.measure = "class",
                alpha = 1, parallel = T)


holdoutAll <- cv.glmnet(data[1:40000,-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))],
                        target[1:40000], family = "binomial", type.measure = "class", alpha = 1, parallel = T)


holdoutControl <- cv.glmnet(dataControl[1:40000,-which(colnames(dataControl) %in% c("numBackers","numAltruistic", "Osuccess"))],
                            target[1:40000], family = "binomial", type.measure = "class", alpha = 1, parallel = T)



print("All Holdout Accuracy")
sum(predict(holdoutAll,
            data[40001:nrow(data),-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))],
            type='class')
    == target[40001:nrow(data)])/(length(target[40001:nrow(data)]))

print("Control Holdout Accuracy")
sum(predict(holdoutControl,
            dataControl[40001:nrow(dataControl),-which(colnames(dataControl) %in% c("numBackers","numAltruistic", "Osuccess"))],
            type='class')
            == target[40001:nrow(dataControl)])/(length(target[40001:nrow(dataControl)]))


topBottomK <- function(cvReg, headers) {
  bestlambda<-cvReg$lambda.min
  mse.min <- cvReg$cvm[cvReg$lambda == bestlambda]
  print(mse.min)
  myCoefs <- coef(cvReg, s=bestlambda)
  myCoefMatrix <- as.matrix(myCoefs)
  print("BOTTOM")
  print(apply(myCoefMatrix, 2, sort)[1:topK,])
  print("TOP")
  print(apply(myCoefMatrix, 2, rsort)[1:topK,])
}

topBottomK(control, controlNames)
topBottomK(all, allNames)
