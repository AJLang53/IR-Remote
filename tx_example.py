import time
import pigpio
import ir_tx

pi = pigpio.pi()

tx = ir_tx.tx(pi, 22, 38000)

tx.clear_code()

tx.add_to_code(46, 11) # Start
tx.add_to_code(23, 11) # 1
tx.add_to_code(11, 11) # 0
tx.add_to_code(11, 11) # 0
tx.add_to_code(23, 11) # 1
tx.add_to_code(11, 11) # 0
tx.add_to_code(23, 11) # 1
tx.add_to_code(11, 11) # 0
tx.add_to_code(23, 11) # 1
tx.add_to_code(11, 11) # 0
tx.add_to_code(11, 11) # 0
tx.add_to_code(23, 11) # 1
tx.add_to_code(11, 11) # 0

tx.send_code()
tx.clear_code()

pi.stop()
