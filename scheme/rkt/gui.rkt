#lang racket

(require 
  slideshow
  racket/class
  racket/gui/base
  "slide.rkt")


(define f (new frame% [label "Keep Goats"]
               [width 400]
               [height 400]
               [alignment '(center center)]))

(send f show #t)

(define (add-drawing p)
  (let ([drawer (make-pict-drawer p)])
    (new canvas% 
         [parent f]
         [style '(border)]
         [paint-callback (lambda (self dc)
                           (drawer dc 0 0))])))


         