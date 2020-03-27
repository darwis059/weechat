# -*- coding: utf-8 -*-
# developed by acidvegas (https://acid.vegas/weechat)

import re
import weechat

valid_nick_re = re.compile(r'([@~&!%+-])?([^\s,\*?\.!@]+)')
colored_nicks = {}

def colorize_nick_color(nick, my_nick):
	if nick == my_nick:
		return weechat.color(weechat.config_string(weechat.config_get('weechat.color.chat_nick_self')))
	else:
		return weechat.info_get('irc_nick_color', nick)

def colorize_cb(data, modifier, modifier_data, line):
	global colored_nicks
	full_name = modifier_data.split(';')[1]
	channel = '.'.join(full_name.split('.')[1:])
	buffer = weechat.buffer_search('', full_name)
	if buffer not in colored_nicks:
		return line
	reset = weechat.color('reset')
	tags_line = modifier_data.rsplit(';')
	if len(tags_line) >= 3:
		tags_line = tags_line[2].split(',')
		for i in ('irc_join','irc_part','irc_quit'):
			if i in tags_line:
				return line
	for words in valid_nick_re.findall(line):
		nick = words[1]
		if len(nick) < 2:
			continue
		if nick not in colored_nicks[buffer]:
			if not nick[-1].isalpha() and not nick[0].isalpha():
				if nick[1:-1] in colored_nicks[buffer]:
					nick = nick[1:-1]
			elif not nick[0].isalpha():
				if nick[1:] in colored_nicks[buffer]:
					nick = nick[1:]
			elif not nick[-1].isalpha():
				if nick[:-1] in colored_nicks[buffer]:
					nick = nick[:-1]
		if nick in colored_nicks[buffer]:
			nick_color = colored_nicks[buffer][nick]
			try:
				cnt = 0
				for word in line.split():
					cnt += 1
					assert cnt < 20
					if word.startswith(('http://', 'https://')):
						continue
					if nick in word:
						biggest_nick = ''
						for i in colored_nicks[buffer]:
							cnt += 1
							assert cnt < 20
							if nick in i and nick != i and len(i) > len(nick):
								if i in word:
									biggest_nick = i
						if len(biggest_nick) > 0 and biggest_nick in word:
							pass
						elif len(word) < len(biggest_nick) or len(biggest_nick) == 0:
							new_word = word.replace(nick, '{0}{1}{2}'.format(nick_color, nick, reset))
							line = line.replace(word, new_word)
			except AssertionError:
				nick_color = colored_nicks[buffer][nick]
				regex = r'(\A|\s).?({0}).?(\Z|\s)'.format(re.escape(nick))
				match = re.search(regex, line)
				if match is not None:
					new_line = line[:match.start(2)] + nick_color+nick+reset + line[match.end(2):]
					line = new_line
	return line

def colorize_input_cb(data, modifier, modifier_data, line):
	global colored_nicks
	buffer = weechat.current_buffer()
	if buffer not in colored_nicks:
		return line
	reset = weechat.color('reset')
	for words in valid_nick_re.findall(line):
		nick = words[1]
		if len(nick) < 2:
			continue
		if nick in colored_nicks[buffer]:
			nick_color = colored_nicks[buffer][nick]
			line = line.replace(nick, '{0}{1}{2}'.format(nick_color, nick, reset))
	return line

def populate_nicks(*args):
	global colored_nicks
	colored_nicks = {}
	buffers = weechat.infolist_get('buffer', '', '')
	while weechat.infolist_next(buffers):
		buffer_ptr = weechat.infolist_pointer(buffers, 'pointer')
		my_nick = weechat.buffer_get_string(buffer_ptr, 'localvar_nick')
		nicklist = weechat.infolist_get('nicklist', buffer_ptr, '')
		while weechat.infolist_next(nicklist):
			if buffer_ptr not in colored_nicks:
				colored_nicks[buffer_ptr] = {}
			if weechat.infolist_string(nicklist, 'type') != 'nick':
				continue
			nick = weechat.infolist_string(nicklist, 'name')
			nick_color = colorize_nick_color(nick, my_nick)
			colored_nicks[buffer_ptr][nick] = nick_color
		weechat.infolist_free(nicklist)
	weechat.infolist_free(buffers)
	return weechat.WEECHAT_RC_OK

def add_nick(data, signal, type_data):
	global colored_nicks
	splitted = type_data.split(',')
	pointer = splitted[0]
	nick = ','.join(splitted[1:])
	if pointer not in colored_nicks:
		colored_nicks[pointer] = {}
	my_nick = weechat.buffer_get_string(pointer, 'localvar_nick')
	nick_color = colorize_nick_color(nick, my_nick)
	colored_nicks[pointer][nick] = nick_color
	return weechat.WEECHAT_RC_OK

def remove_nick(data, signal, type_data):
	global colored_nicks
	splitted = type_data.split(',')
	pointer = splitted[0]
	nick = ','.join(splitted[1:])
	if pointer in colored_nicks and nick in colored_nicks[pointer]:
		del colored_nicks[pointer][nick]
	return weechat.WEECHAT_RC_OK

if weechat.register('colorize_nicks', 'acidvegas', '1.0', 'ISC', 'colorize nicks', '', ''):
	populate_nicks()
	weechat.hook_signal('nicklist_nick_added', 'add_nick', '')
	weechat.hook_signal('nicklist_nick_removed', 'remove_nick', '')
	weechat.hook_modifier('weechat_print', 'colorize_cb', '')
	weechat.hook_config('weechat.color.chat_nick_colors', 'populate_nicks', '')
	weechat.hook_config('weechat.look.nick_color_hash', 'populate_nicks', '')
	weechat.hook_modifier('colorize_nicks', 'colorize_cb', '')
	weechat.hook_modifier('250|input_text_display', 'colorize_input_cb', '')