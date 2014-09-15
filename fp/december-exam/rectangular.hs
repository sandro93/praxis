import Data.List
maximum' :: (Ord a) => [a] -> a
maximum' = foldr1(\x acc -> if x > acc then x else acc)

square :: Double -> Double
square x = x * x

distance :: (Double, Double) -> (Double, Double) -> Double
distance (x1, y1) (x2, y2) = sqrt (square (x2 - x1) + square (y2 - y1))

sides :: (Double, Double) -> (Double, Double) -> (Double, Double) -> [Double]
sides (x1, y1) (x2, y2) (x3, y3) = reverse (sort [distance a b | (a, b) <- [((x1, y1),(x2, y2)), ((x1, y1), (x3, y3)), ((x2,y2), (x3, y3))]])

isRectangular :: (Double, Double) -> (Double, Double) -> (Double, Double) -> Bool
isRectangular (x1,y1) (x2, y2) (x3, y3) = if square (head (sides (x1, y1) (x2, y2) (x3, y3))) == sum (map square (tail (sides (x1, y1) (x2, y2) (x3, y3)))) then True else False


squares :: (Double, Double) -> (Double, Double) -> (Double, Double) -> Bool
squares (x1,y1) (x2, y2) (x3, y3) = (sum (map square (tail (sides (x1, y1) (x2, y2) (x3, y3))))) == (sum (map square (tail (sides (x1, y1) (x2, y2) (x3, y3))))) 


{-
isRectangular :: (Double, Double) -> (Double, Double) -> (Double, Double) -> Bool
isRectangular (x1,y1) (x2, y2) (x3, y3) 
  | distance (x1, y1) (x2, y2) > distance (x2, y2) (x3, y3) && distance (x1, y1) (x2, y2) > distance (x1, y1) (x3, y3) = 

-}



