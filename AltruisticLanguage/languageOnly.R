setwd("/home/jack/Desktop/NLP/CS6742/AltruisticLanguage")
library('Matrix')
library('glmnet')
library('foreach')
library('doParallel')
registerDoParallel()
rsort <- function(x) {
  sort(x, decreasing = TRUE)
}

###
train <- 600
data <- readMM("photoSmall.mtx")
headers <- read.csv("photoSmall.csv")
colnames(data) <- colnames(headers)
target <- data[,c("numBackers", "numAltruistic")]
target <- target[,2]/target[,1]
target[is.nan(target)] <- 0
target <- target > .1
setwd("ContentModel")
posProbs <- t(read.csv("succ.csv", header=F))
negProbs <- t(read.csv("fail.csv", header=F))
setwd("..")
colnames(posProbs) <- c("PosProb")
colnames(negProbs) <- c("NegProb")
data <- cBind(data, negProbs)
data <- cBind(data, posProbs)
trainData <- data[1:train, -which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))]
#trainData <- trainData[-which(posProbs==0),]
trainTarget <- target[1:train]
#trainTarget <- trainTarget[-which(posProbs==0)]
######
control <- cv.glmnet(trainData[,c(-which(colnames(trainData) %in% c("PosProb", "NegProb")), -grep("^T", colnames(trainData)))],
                     trainTarget , family = "binomial", type.measure = "class", alpha = 0, parallel = F)

holdoutNoCM <- cv.glmnet(trainData[,],#-which(colnames(trainData) %in% c("PosProb", "NegProb"))],
                        trainTarget , family = "binomial", type.measure = "class", alpha = 0, parallel = F)

holdout <- cv.glmnet(trainData,
                    trainTarget , family = "binomial", type.measure = "class", alpha = 0, parallel = F)

holdoutNoText <- cv.glmnet(trainData[,-grep("^T", colnames(trainData))],
                           trainTarget , family = "binomial", type.measure = "class", alpha = 0, parallel = F)
######
predControl <- predict(control,
                       data[(train+1):nrow(data), c(-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess", "PosProb", "NegProb")),
                                              -grep("^T", colnames(data)))], type='class')

predHO <- predict(holdout,
                data[(train+1):nrow(data),-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess"))],
                type='class')

predNOCM <- predict(holdoutNoCM,
                    data[(train+1):nrow(data),-which(colnames(data) %in% c("numBackers","numAltruistic",
                                                                    "Osuccess"))],#, "PosProb", "NegProb"))],
                    type='class')

predNOTXT <- predict(holdoutNoText,
                    data[(train+1):nrow(data), c(-which(colnames(data) %in% c("numBackers","numAltruistic", "Osuccess")),-grep("^T", colnames(data)))],
                    type='class')
######

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
print("Controls Only (No Text or CM)")
checkModel(predControl)
print("Controls + CM (No Text)")
checkModel(predNOTXT)
print("Controls + Text (No CM)")
checkModel(predNOCM)
print("Everything (Controls + Text + CM)")
checkModel(predHO)

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
topK <- 10
topBottomK(holdoutNoText, topK)
