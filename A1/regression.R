setwd("./Desktop/NLP/git/A1")
result <- rep(0, 15)
for(i in 0:14)
{
  docName <- paste(toString(i), ".csv", sep="")
  data <- read.csv(docName)
  colnames(data) <- c("Uniqueness", "Helpful")
  myModel <- glm(Helpful ~ Uniqueness, data = data,
                 family = "binomial")
  result[i] <- coef(summary(myModel))[,"Pr(>|z|)"][2]
}
