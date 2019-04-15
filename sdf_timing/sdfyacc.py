import ply.yacc as yacc
import utils

from sdf_timing.sdflex import tokens

timings = dict()

header = dict()
delays_list = list()
cells = dict()

tmp_delay_list = list()
tmp_equation = list()
tmp_constr_list = list()


def remove_quotation(s):
    return s.replace('"', '')


def p_sdf_file(p):
    '''sdf_file : LPAR DELAYFILE sdf_header RPAR
                | LPAR DELAYFILE sdf_header cell_list RPAR'''

    timings['header'] = p[3]
    if p[4] != ')':
        timings['cells'] = p[4]

    p[0] = timings


def p_sdf_header(p):
    '''sdf_header : sdf_header_qstring
                  | sdf_header_qfloat
                  | sdf_header sdf_header_qstring
                  | sdf_header sdf_header_qfloat
                  | sdf_header voltage
                  | sdf_header temperature
                  | sdf_header hierarchy_divider
                  | sdf_header timescale'''

    p[0] = p[1]


def p_sdf_header_qstring(p):
    '''sdf_header_qstring : LPAR qstring_header_entry QSTRING RPAR
                          | LPAR qstring_header_entry RPAR'''
    if len(p) == 5:
        header[p[2].lower()] = remove_quotation(p[3])
        p[0] = header


def p_qstring_header_entry(p):
    '''qstring_header_entry : SDFVERSION
                            | DATE
                            | PROCESS
                            | DESIGN
                            | VENDOR
                            | PROGRAM
                            | VERSION'''
    p[0] = p[1]


def p_sdf_header_qfloat(p):
    'sdf_header_qfloat : LPAR qfloat_header_entry QFLOAT RPAR'
    if len(p) == 5:
        header[p[2].lower()] = remove_quotation(str(p[3]))
        p[0] = header


def p_qfloat_header_entry(p):
    '''qfloat_header_entry : SDFVERSION
                           | VERSION'''
    p[0] = p[1]


def p_sdf_voltage(p):
    'voltage : LPAR VOLTAGE real_triple RPAR'
    header['voltage'] = p[3]
    p[0] = header


def p_sdf_temperature(p):
    'temperature : LPAR TEMPERATURE real_triple RPAR'
    header['temperature'] = p[3]
    p[0] = header


def p_sdf_divider(p):
    '''hierarchy_divider : LPAR DIVIDER DOT RPAR
               | LPAR DIVIDER SLASH RPAR'''
    header['divider'] = p[3]
    p[0] = header


def p_sdf_timescale(p):
    'timescale : LPAR TIMESCALE FLOAT STRING RPAR'
    header['timescale'] = str(p[3]) + p[4]
    p[0] = header


def p_cell_list(p):
    '''cell_list : cell
                 | cell_list cell'''
    p[0] = p[1]


def add_delays_to_cell(celltype, instance, delays):

    if delays is None:
        return
    for delay in delays:
        cells[celltype][instance][delay['name']] = delay


def add_cell(name, instance):

    # name
    if name not in cells:
        cells[name] = dict()
    # instance
    if instance not in cells[name]:
        cells[name][instance] = dict()


def p_timing_cell(p):
    '''cell : LPAR CELL celltype instance timing_check RPAR
            | LPAR CELL celltype instance RPAR
            | LPAR CELL celltype instance delay_lst timing_check RPAR
            | LPAR CELL celltype instance delay_lst RPAR
            | LPAR CELL celltype instance timingenv_lst RPAR'''

    add_cell(p[3], p[4])
    add_delays_to_cell(p[3], p[4], delays_list)
    p[0] = cells
    delays_list[:] = []


def p_celltype(p):
    'celltype : LPAR CELLTYPE QSTRING RPAR'
    p[0] = remove_quotation(p[3])


def p_instance(p):
    '''instance : LPAR INSTANCE STRING RPAR
                | LPAR INSTANCE RPAR'''
    if p[3] == ')':
        p[0] = None
    else:
        p[0] = p[3]


def p_timing_check(p):
    '''timing_check : LPAR TIMINGCHECK timing_check_list RPAR'''


def p_timing_port(p):
    '''timing_port : port_check
                   | cond_check'''
    p[0] = p[1]


def p_port_check(p):
    'port_check : port_spec'
    port = dict()
    port['cond'] = False
    port['cond_equation'] = None
    port['port'] = p[1]
    p[0] = port


def p_timing_cond(p):
    'cond_check : LPAR COND equation port_spec RPAR'
    port = dict()
    port['cond'] = True
    port['cond_equation'] = " ".join(p[3])
    port['port'] = p[4]
    p[0] = port


def p_timing_check_list(p):
    '''timing_check_list : t_check
                         | timing_check_list t_check'''
    if len(p) == 2:
        delays_list.extend(list(p[1]))
    else:
        delays_list.extend(list(p[2]))
    tmp_delay_list[:] = []


def p_t_check(p):
    '''t_check : removal_check
               | recovery_check
               | hold_check
               | setup_check
               | width_check
               | setuphold_check'''
    p[0] = p[1]


def p_removal_check(p):
    'removal_check : LPAR REMOVAL timing_port timing_port real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('removal', p[3], p[4], paths)
    tmp_delay_list.append(tcheck)
    p[0] = tmp_delay_list


def p_recovery_check(p):
    'recovery_check : LPAR RECOVERY timing_port timing_port real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('recovery', p[3], p[4], paths)
    tmp_delay_list.append(tcheck)
    p[0] = tmp_delay_list


def p_hold_check(p):
    'hold_check : LPAR HOLD timing_port timing_port real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('hold', p[3], p[4], paths)
    tmp_delay_list.append(tcheck)
    p[0] = tmp_delay_list


def p_setup_check(p):
    'setup_check : LPAR SETUP timing_port timing_port real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('setup', p[3], p[4], paths)
    tmp_delay_list.append(tcheck)
    p[0] = tmp_delay_list


def p_width_check(p):
    'width_check : LPAR WIDTH timing_port real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[4]
    tcheck = utils.add_tcheck('width', p[3], p[3], paths)
    tmp_delay_list.append(tcheck)
    p[0] = tmp_delay_list


def p_setuphold_check(p):
    'setuphold_check : LPAR SETUPHOLD timing_port timing_port real_triple \
    real_triple RPAR'

    paths = dict()
    paths['setup'] = p[5]
    paths['hold'] = p[6]
    tcheck = utils.add_tcheck('setup', p[3], p[4], paths)
    tmp_delay_list.append(tcheck)
    p[0] = tmp_delay_list


def p_timingenv_list(p):
    '''timingenv_lst : timingenv
                     | timingenv_lst timingenv'''


def p_timingenv(p):
    'timingenv : LPAR TIMINGENV constraints_list RPAR'


def p_constraints_list(p):
    '''constraints_list : path_constraint
                        | constraints_list path_constraint'''
    if len(p) == 2:
        delays_list.extend(p[1])
    else:
        delays_list.extend(p[2])
    tmp_constr_list[:] = []


def p_path_constraint(p):
    'path_constraint : LPAR PATHCONSTRAINT port_spec port_spec real_triple \
    real_triple RPAR'

    paths = dict()
    paths['rise'] = p[5]
    paths['fall'] = p[6]
    constr = utils.add_constraint('pathconstraint', p[3], p[4], paths)
    tmp_constr_list.append(constr)
    p[0] = tmp_constr_list


def p_delay_list(p):
    '''delay_lst : delay
                 | delay_lst delay'''


def p_delay(p):
    '''delay : LPAR DELAY absolute_list RPAR
             | LPAR DELAY increment_list RPAR'''


def p_absolute_list(p):
    '''absolute_list : absolute
                     | absolute_list absolute'''


def p_absolute_empty(p):
    'absolute : LPAR ABSOLUTE RPAR'


def p_absolute_delay_list(p):
    '''absolute : LPAR ABSOLUTE delay_list RPAR
                | LPAR ABSOLUTE cond_delay RPAR'''
    for d in p[3]:
        d['is_absolute'] = True
    delays_list.extend(list(p[3]))
    tmp_delay_list[:] = []


def p_increment_list(p):
    '''increment_list : increment
                      | increment_list increment'''


def p_increment_delay_list(p):
    '''increment : LPAR INCREMENT delay_list RPAR
                 | LPAR INCREMENT cond_delay RPAR'''
    for d in p[3]:
        d['is_increment'] = True
    delays_list.extend(list(p[3]))
    tmp_delay_list[:] = []


def p_cond_delay(p):
    'cond_delay : LPAR COND delay_condition delay_list RPAR'
    # add condition to every list alement
    for d in p[4]:
        d['is_cond'] = True
        d['cond_equation'] = " ".join(p[3])
    p[0] = p[4]


def p_delay_condition(p):
    'delay_condition : LPAR equation RPAR'
    p[0] = list(p[2])
    tmp_equation[:] = []


def p_delay_condition_nopar(p):
    'delay_condition : equation'
    p[0] = list(p[1])
    tmp_equation[:] = []


def p_delay_list_interconnect(p):
    '''delay_list : del
                  | delay_list del'''
    if len(p) == 2:
        tmp_delay_list.append(p[1])
    else:
        tmp_delay_list.append(p[2])

    p[0] = tmp_delay_list


def p_del(p):
    '''del : interconnect
           | iopath
           | port'''
    p[0] = p[1]


def p_iopath(p):
    'iopath : LPAR IOPATH port_spec port_spec real_triple real_triple RPAR'
    paths = dict()
    paths['fast'] = p[5]
    paths['slow'] = p[6]
    iopath = utils.add_iopath(p[3], p[4], paths)
    p[0] = iopath


def p_port_spec(p):
    '''port_spec : STRING
                 | LPAR port_condition STRING RPAR
                 | FLOAT'''

    if p[1] != '(':
        p[0] = str(p[1])
    else:
        p[0] = p[3]


def p_interconnect(p):
    'interconnect : LPAR INTERCONNECT port_spec port_spec real_triple \
    real_triple RPAR'
    paths = dict()
    paths['fast'] = p[5]
    paths['slow'] = p[6]
    interconnect = utils.add_interconnect(p[3], p[4], paths)
    p[0] = interconnect


def p_interconnect_single(p):
    'interconnect : LPAR INTERCONNECT port_spec port_spec real_triple \
    RPAR'
    paths = dict()
    paths['nominal'] = p[5]
    interconnect = utils.add_interconnect(p[3], p[4], paths)
    p[0] = interconnect


def p_port_single(p):
    'port : LPAR PORT port_spec real_triple RPAR'
    paths = dict()
    paths['nominal'] = p[4]
    port = utils.add_port(p[3], paths)
    p[0] = port


def p_port_double(p):
    'port : LPAR PORT port_spec real_triple real_triple RPAR'
    paths = dict()
    paths['fast'] = p[4]
    paths['slow'] = p[5]
    port = utils.add_port(p[3], paths)
    p[0] = port


def p_port_triple(p):
    'port : LPAR PORT port_spec real_triple real_triple real_triple RPAR'
    paths = dict()
    paths['fast'] = p[4]
    paths['nominal'] = p[5]
    paths['slow'] = p[6]
    port = utils.add_port(p[3], paths)
    p[0] = port


def p_port_condition(p):
    '''port_condition : POSEDGE
                      | NEGEDGE'''
    p[0] = p[1]


def p_real_triple_no_par(p):
    '''real_triple : FLOAT COLON FLOAT COLON FLOAT
                   | FLOAT COLON COLON FLOAT
                   | COLON FLOAT COLON'''
    delays_triple = dict()
    if len(p) > 4:
        if p[3] == ':':
            delays_triple['min'] = float(p[1])
            delays_triple['avg'] = None
            delays_triple['max'] = float(p[4])
        else:
            delays_triple['min'] = float(p[1])
            delays_triple['avg'] = float(p[3])
            delays_triple['max'] = float(p[5])
    else:
        delays_triple['min'] = None
        delays_triple['avg'] = p[2]
        delays_triple['max'] = None

    p[0] = delays_triple


def p_real_triple(p):
    '''real_triple : LPAR FLOAT COLON FLOAT COLON FLOAT RPAR
                   | LPAR RPAR
                   | LPAR FLOAT COLON COLON FLOAT RPAR
                   | LPAR COLON FLOAT COLON RPAR'''

    delays_triple = dict()
    if len(p) > 3:
        if p[4] == ':':
            if p[2] == ':':
                delays_triple['min'] = None
                delays_triple['avg'] = float(p[3])
                delays_triple['max'] = None
            else:
                delays_triple['min'] = float(p[2])
                delays_triple['avg'] = None
                delays_triple['max'] = float(p[5])
        else:
            delays_triple['min'] = float(p[2])
            delays_triple['avg'] = float(p[4])
            delays_triple['max'] = float(p[6])
    else:
        delays_triple['min'] = None
        delays_triple['avg'] = None
        delays_triple['max'] = None

    p[0] = delays_triple


def p_equation(p):
    '''equation : operator
                | STRING
                | FLOAT
                | equation operator
                | equation FLOAT
                | equation STRING'''
    if len(p) == 2:
        tmp_equation.append(p[1])
    else:
        tmp_equation.append(p[2])

    p[0] = tmp_equation


def p_operator(p):
    '''operator : ARITHMETIC
                | SLASH
                | MODULO
                | LOGIC_NOT
                | BIT_NOT
                | LOGIC_AND
                | BIT_AND
                | NAND
                | LOGIC_OR
                | BIT_OR
                | NOR
                | XOR
                | XNOR
                | EQUAL
                | NEQUAL
                | CASEEQUAL
                | CASENEQUAL
                | LEFTSHIFT
                | RIGHTSHIFT
                | GT
                | LT
                | GTE
                | LTE'''
    p[0] = p[1]


def p_error(p):
    raise Exception("Syntax error at '%s' line: %d" % (p.value, p.lineno))


parser = yacc.yacc(debug=False, write_tables=False)
