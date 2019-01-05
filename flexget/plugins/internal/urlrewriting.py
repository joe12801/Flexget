from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

import logging

from flexget import plugin
from flexget.event import event

log = logging.getLogger('urlrewriter')


class UrlRewritingError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class PluginUrlRewriting(object):
    """
    Provides URL rewriting framework
    """

    def on_task_urlrewrite(self, task, config):
        log.debug('Checking %s entries', len(task.accepted))
        # try to urlrewrite all accepted
        for entry in task.accepted:
            try:
                self.url_rewrite(task, entry)
            except UrlRewritingError as e:
                log.warning(e.value)
                entry.fail()

    # API method
    def url_rewritable(self, task, entry):
        """Return True if entry is urlrewritable by registered rewriter."""
        for urlrewriter in plugin.get_plugins(interface='urlrewriter'):
            log.trace('checking urlrewriter %s', urlrewriter.name)
            if urlrewriter.instance.url_rewritable(task, entry):
                return True
        return False

    # API method - why priority though?
    @plugin.priority(255)
    def url_rewrite(self, task, entry):
        """Rewrites given entry url. Raises UrlRewritingError if failed."""
        tries = 0
        while self.url_rewritable(task, entry) and entry.accepted:
            tries += 1
            if tries > 20:
                raise UrlRewritingError('URL rewriting was left in infinite loop while rewriting url for %s, '
                                        'some rewriter is returning always True' % entry)
            for urlrewriter in plugin.get_plugins(interface='urlrewriter'):
                name = urlrewriter.name
                try:
                    if urlrewriter.instance.url_rewritable(task, entry):
                        old_url = entry['url']
                        log.debug('Url rewriting %s' % entry['url'])
                        urlrewriter.instance.url_rewrite(task, entry)
                        if entry['url'] != old_url:
                            if entry.get('urls') and old_url in entry.get('urls'):
                                entry['urls'][entry['urls'].index(old_url)] = entry['url']
                            log.info('Entry \'%s\' URL rewritten to %s (with %s)', entry['title'], entry['url'], name)
                except UrlRewritingError as r:
                    # increase failcount
                    # count = self.shared_cache.storedefault(entry['url'], 1)
                    # count += 1
                    raise UrlRewritingError('URL rewriting %s failed: %s' % (name, r.value))
                except plugin.PluginError as e:
                    raise UrlRewritingError('URL rewriting %s failed: %s' % (name, e.value))
                except Exception as e:
                    log.exception(e)
                    raise UrlRewritingError('%s: Internal error with url %s' % (name, entry['url']))


class DisableUrlRewriter(object):
    """Disable certain urlrewriters."""

    schema = {
        'deprecated': '`disable_urlrewriters` plugin is deprecated, use `disable` plugin instead',
        'type': 'array',
        'items': {'type': 'string'}
    }

    def on_task_start(self, task, config):
        disable = plugin.get_plugin_by_name('disable')['instance']
        disable.on_task_start(task, config)

    def on_task_exit(self, task, config):
        disable = plugin.get_plugin_by_name('disable')['instance']
        disable.on_task_exit(task, config)

    on_task_abort = on_task_exit


@event('plugin.register')
def register_plugin():
    plugin.register(PluginUrlRewriting, 'urlrewriting', builtin=True, api_ver=2)
    plugin.register(DisableUrlRewriter, 'disable_urlrewriters', api_ver=2)
    plugin.register_task_phase('urlrewrite', before='download')
