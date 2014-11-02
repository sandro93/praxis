#lang racket/base
(provide posn posn-x posn-y posn-mv)
(struct posn (x y))
(define (posn-mv p dx dy)
  (posn (+ (posn-x p) dx)
	(+ (posn-y p) dy)))
