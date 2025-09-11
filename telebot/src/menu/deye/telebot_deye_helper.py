from typing import List
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from single_register import SingleRegister
from deye_registers_holder import DeyeRegistersHolder
from deye_system_work_mode import DeyeSystemWorkMode
from deye_gen_port_mode import DeyeGenPortMode

holder_kwargs = {
  'name': 'telebot',
  'socket_timeout': 7,
  'caching_time': 15,
#  'verbose': True,
}

def get_register_values(registers: List[DeyeRegister]):
  result = ""
  for register in registers:
    if isinstance(register.value, DeyeSystemWorkMode) or isinstance(register.value, DeyeGenPortMode):
      val = register.value.pretty
    else:
      val = str(register.value).title()

    desc = register.description.replace('Inverter ', '')
    desc = desc.replace('Grid Charging Start SOC', 'Max Charge SOC')
    result += f'{desc}: {val} {register.suffix}\n'

  return result

def write_register(register: DeyeRegister, value):
  loggers = DeyeLoggers()

  def creator(prefix):
    return SingleRegister(None, prefix)

  try:
    holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
    holder.connect_and_read()
    value = holder.write_register(register, value)
    return value
  except Exception as e:
    raise Exception(str(e))
  finally:
    holder.disconnect()
