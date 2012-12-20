from __future__ import unicode_literals, division, absolute_import
import logging
from flexget.plugin import register_plugin, register_parser_option, priority
from flexget.utils.tools import console

log = logging.getLogger('dump')


def dump(entries, debug=False, eval_lazy=False):
    """
    Dump *entries* to stdout

    :param list entries: Entries to be dumped.
    :param bool debug: Print non printable fields as well.
    :param bool eval_lazy: Evaluate lazy fields.
    """

    invalid = object()
    for entry in entries:
        #c = entry.copy()
        #sanitize(c)
        #print yaml.safe_dump(entry)
        for field in sorted(entry):
            value = invalid
            if entry.is_lazy(field):
                if eval_lazy:
                    value = entry[field]
                else:
                    value = '<LazyField - value will be determined when it\'s accessed>'
            else:
                value = entry[field]
            assert value is not invalid
            if isinstance(value, basestring):
                try:
                    console('%-17s: %s' % (field, value.replace('\r', '').replace('\n', '')))
                except:
                    console('%-17s: %s (warning: unable to print)' % (field, repr(value)))
            elif isinstance(value, (int, float, list, dict)):
                console('%-17s: %s' % (field, value))
            elif value is None:
                console('%-17s: %s' % (field, value))
            else:
                if debug:
                    console('%-17s: [not printable] (%s)' % (field, value))
        console('')


class OutputDump(object):
    """
    Outputs all entries to console
    """

    def validator(self):
        from flexget import validator
        return validator.factory('boolean')

    @priority(0)
    def on_task_output(self, task):
        if 'dump' not in task.config and not task.manager.options.dump_entries:
            return
        #from flexget.utils.tools import sanitize
        #import yaml

        eval_lazy = task.manager.options.dump_entries == 'eval'
        undecided = [entry for entry in task.entries if not entry in task.accepted]
        if undecided:
            console('-- Undecided: --------------------------')
            dump(undecided, task.manager.options.debug, eval_lazy)
        if task.accepted:
            console('-- Accepted: ---------------------------')
            dump(task.accepted, task.manager.options.debug, eval_lazy)
        if task.rejected:
            console('-- Rejected: ---------------------------')
            dump(task.rejected, task.manager.options.debug, eval_lazy)

register_plugin(OutputDump, 'dump', builtin=True)
register_parser_option('--dump', nargs='?', choices=['eval'], const=True, dest='dump_entries',
                       help='Display all entries in task with details. '
                            'Arg `--dump eval` will evaluate all lazy fields.')
