library(plotrix)

n <- 300
values <- rep(0, n)
U <- rep(0, n)
L <- rep(0, n)
for(i in 0:(n-1))
{
  docName <- paste("temp/", toString(i), ".csv", sep="")
  data <- read.csv(docName)
  colnames(data) <- c("Uniqueness", "Helpful")
  myModel <- glm(Helpful ~ Uniqueness, data = data,
                 family = "binomial")
  confInt <- confint(myModel)[2,]
  L[i] <- confInt[[1]]
  U[i] <- confInt[[2]]
  values[i] <- coef(myModel)[[2]]
}
productIds <- read.csv("productIds.txt", header=F)
plotCI(values, ui=U, li=L, pch=".", xlab = "Review Index", ylab = "Influence of Uniqueness",
        main = "Influence of Uniqueness on Helpfulness of Reviews for the Top 300 Products",
        xlim = c(1,300),
        ylim = c(-30, 20))
meanConfInt <- t.test(values)$conf.int
abline(h=meanConfInt[[1]], col=2, lty=2, lwd = 4)
abline(h=mean(values), col=2)
abline(h=meanConfInt[[2]], col=2, lty=2, lwd = 4)
abline(h=0, col=3, lty=1, lwd = 3)
