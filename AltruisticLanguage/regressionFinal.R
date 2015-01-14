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
data <- readMM("all.mtx")
headers <- read.csv("all.csv")
setwd("..")

colnames(data) <- colnames(headers)
colnames(dataControl) <- colnames(headersControl)

target <- data[,c("numBackers", "numAltruistic")]
target <- target[,2]/target[,1]
target[is.nan(target)] <- 0
target <- target > .1

control <- cv.glmnet(data[,c(-grep("^T|^L", colnames(data)), -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess")))], target,
              family = "binomial",
              type.measure = "class",
              alpha = 1, parallel = T)

langControl <- cv.glmnet(data[,c(-grep("^T", colnames(data)), -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess")))], target,
                         family = "binomial",
                         type.measure = "class",
                         alpha = 1, parallel = T)

total <- cv.glmnet(data[,-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))], target,
                family = "binomial",
                type.measure = "class",
                alpha = 1, parallel = T)

train <- 40000

holdoutControl <- cv.glmnet(data[1:train,c(-grep("^T|^L", colnames(data)), -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess")))],
                        target[1:train], family = "binomial", type.measure = "class", alpha = 1, parallel = T)

holdoutLangControl <- cv.glmnet(data[1:train,c(-grep("^T", colnames(data)), -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess")))],
                        target[1:train], family = "binomial", type.measure = "class", alpha = 1, parallel = T)

holdoutTotal <- cv.glmnet(dataControl[1:train,-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))],
                              target[1:train], family = "binomial", type.measure = "class", alpha = 1, parallel = T)


predControl <- predict(holdoutControl,
            data[(train+1):nrow(data),c(-grep("^T|^L", colnames(data)), -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess")))],
            type='class')

predLangControl <- predict(holdoutLangControl,
                           data[(train+1):nrow(data),
                                    c(-grep("^T", colnames(data)), -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess")))],
                           type='class')

predTotal <- predict(holdoutTotal,
                     data[(train+1):nrow(data), -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))],
                     type='class')

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

checkModel <- function(pred) { 
  print("Accuracy")
  print(sum(pred == target[(train+1):nrow(data)])/(length(target[(train+1):nrow(data)])))
  posCor <- sum(pred[target[(train+1):nrow(data)]==1] == target[(train+1):nrow(data)][target[(train+1):nrow(data)]==1])
  negCor <- sum(pred[target[(train+1):nrow(data)]==0] == target[(train+1):nrow(data)][target[(train+1):nrow(data)]==0])
  posFail <- sum(pred[target[(train+1):nrow(data)]==1] != target[(train+1):nrow(data)][target[(train+1):nrow(data)]==1])
  negFail <- sum(pred[target[(train+1):nrow(data)]==0] != target[(train+1):nrow(data)][target[(train+1):nrow(data)]==0])
  perc <- posCor/(posCor + negFail)
  rec <- posCor/(posCor + posFail)
  f <- 2 * perc * rec / (perc + rec)
  print("Percision")
  print(perc)
  print("Recall")
  print(rec)
  print("F-measure")
  print(f)
}

orderedCoefs <- function(cvReg) {
  bestlambda<-cvReg$lambda.min
  mse.min <- cvReg$cvm[cvReg$lambda == bestlambda]
  print(1-mse.min)
  myCoefs <- coef(cvReg, s=bestlambda)
  myCoefMatrix <- as.matrix(myCoefs)
  return(apply(myCoefMatrix, 2, sort))
}


checkModel(predControl)
checkModel(predLangControl)

topK <- 50
topBottomK(control, topK)
topBottomK(langControl, topK)
topBottomK(SW, topK)
topBottomK(test2, topK)
write.table(orderedCoefs(SW), file = "testFile.csv")