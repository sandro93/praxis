(defun double (number)
  "Double the number"
  (interactive "p")
  (message "%d * 2 = %d" number (* 2 number)))

(double 4)

(defun check-fill-column (number)
  "test whether the current value of `full-column' is greater than the argument."
  (interactive "p")
  (if (> fill-column number)
      (message "current value of the `fill-column' is %d." fill-column)
    (message "all is OK")))