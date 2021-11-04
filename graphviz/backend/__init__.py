"""Execute rendering subprocesses and open files in viewer."""

import logging
import os
import pathlib
import re
import subprocess
import typing

from ..encoding import DEFAULT_ENCODING as ENCODING
from .. import copying
from .common import RequiredArgumentError
from .running import run_check, ExecutableNotFound
from .unflattening import unflatten
from .viewing import view, View

__all__ = ['DOT_BINARY', 'UNFLATTEN_BINARY',
           'ENGINES', 'FORMATS', 'RENDERERS', 'FORMATTERS',
           'RequiredArgumentError',
           'render', 'pipe', 'pipe_string', 'pipe_lines', 'pipe_lines_string',
           'unflatten',
           'Graphviz',
           'version', 'view',
           'View',
           'ExecutableNotFound']

#: :class:`pathlib.Path` of layout command (``Path('dot')``).
DOT_BINARY = pathlib.Path('dot')



ENGINES = {'dot',  # http://www.graphviz.org/pdf/dot.1.pdf
           'neato',
           'twopi',
           'circo',
           'fdp',
           'sfdp',
           'patchwork',
           'osage'}


FORMATS = {'bmp',  # http://www.graphviz.org/doc/info/output.html
           'canon', 'dot', 'gv', 'xdot', 'xdot1.2', 'xdot1.4',
           'cgimage',
           'cmap',
           'eps',
           'exr',
           'fig',
           'gd', 'gd2',
           'gif',
           'gtk',
           'ico',
           'imap', 'cmapx',
           'imap_np', 'cmapx_np',
           'ismap',
           'jp2',
           'jpg', 'jpeg', 'jpe',
           'json', 'json0', 'dot_json', 'xdot_json',  # Graphviz 2.40
           'pct', 'pict',
           'pdf',
           'pic',
           'plain', 'plain-ext',
           'png',
           'pov',
           'ps',
           'ps2',
           'psd',
           'sgi',
           'svg', 'svgz',
           'tga',
           'tif', 'tiff',
           'tk',
           'vml', 'vmlz',
           'vrml',
           'wbmp',
           'webp',
           'xlib',
           'x11'}

RENDERERS = {'cairo',  # $ dot -T:
             'dot',
             'fig',
             'gd',
             'gdiplus',
             'map',
             'pic',
             'pov',
             'ps',
             'svg',
             'tk',
             'vml',
             'vrml',
             'xdot'}

FORMATTERS = {'cairo',
              'core',
              'gd',
              'gdiplus',
              'gdwbmp',
              'xlib'}


log = logging.getLogger(__name__)


def command(engine: str, format_: str,
            *, renderer: typing.Optional[str] = None,
            formatter: typing.Optional[str] = None
            ) -> typing.List[typing.Union[os.PathLike, str]]:
    """Return ``subprocess.Popen`` args list for rendering."""
    if formatter is not None and renderer is None:
        raise RequiredArgumentError('formatter given without renderer')

    if engine not in ENGINES:
        raise ValueError(f'unknown engine: {engine!r}')
    if format_ not in FORMATS:
        raise ValueError(f'unknown format: {format_!r}')
    if renderer is not None and renderer not in RENDERERS:
        raise ValueError(f'unknown renderer: {renderer!r}')
    if formatter is not None and formatter not in FORMATTERS:
        raise ValueError(f'unknown formatter: {formatter!r}')

    output_format = [f for f in (format_, renderer, formatter) if f is not None]
    output_format_flag = ':'.join(output_format)
    return [DOT_BINARY, f'-K{engine}', f'-T{output_format_flag}']


def render(engine: str, format: str,
           filepath: typing.Union[os.PathLike, str],
           renderer: typing.Optional[str] = None,
           formatter: typing.Optional[str] = None,
           quiet: bool = False) -> str:
    """Render file with Graphviz ``engine`` into ``format``,
        return result filename.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        filepath: Path to the DOT source file to render.
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        The (possibly relative) path of the rendered file.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Note:
        The layout command is started from the directory of ``filepath``,
        so that references to external files
        (e.g. ``[image=images/camelot.png]``)
        can be given as paths relative to the DOT source file.
    """
    dirname, filename = os.path.split(filepath)
    del filepath

    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    cmd.extend(['-O', filename])

    suffix = '.'.join(f for f in (formatter, renderer, format) if f is not None)
    rendered = f'{filename}.{suffix}'

    if dirname:
        cwd = dirname
        rendered = os.path.join(dirname, rendered)
    else:
        cwd = None

    run_check(cmd, capture_output=True, cwd=cwd, quiet=quiet)
    return rendered


def pipe(engine: str, format: str, data: bytes,
         renderer: typing.Optional[str] = None,
         formatter: typing.Optional[str] = None,
         quiet: bool = False) -> bytes:
    """Return ``data`` (``bytes``) piped through Graphviz ``engine``
        into ``format`` as ``bytes``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        data: Binary (encoded) DOT source bytes to render.
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Binary (encoded) stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe('dot', 'svg', b'graph { hello -- world }')[:14]
        b'<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input': data}

    proc = run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_string(engine: str, format: str, input_string: str,
               *, encoding: str,
                renderer: typing.Optional[str] = None,
                formatter: typing.Optional[str] = None,
                quiet: bool = False) -> str:
    """Return ``input_string`` piped through Graphviz ``engine``
        into ``format`` as ``str``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_string: Binary (encoded) DOT source bytes to render.
        encoding: Encoding to en/decode subprocess stdin and stdout (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Decoded stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe_string('dot', 'svg', 'graph { spam }',
        ...                      encoding='ascii')[:14]
        '<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input': input_string, 'encoding': encoding}

    proc = run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_lines(engine: str, format: str, input_lines: typing.Iterator[str],
               *, input_encoding: str,
               renderer: typing.Optional[str] = None,
               formatter: typing.Optional[str] = None,
               quiet: bool = False) -> bytes:
    r"""Return ``input_lines`` piped through Graphviz ``engine``
        into ``format`` as ``bytes``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_lines: DOT source lines to render (including final newline).
        input_encoding: Encode input_lines for subprocess stdin (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Binary stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe_lines('dot', 'svg', iter(['graph { spam }\n']),
        ...                     input_encoding='ascii')[:14]
        b'<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input_lines': (line.encode(input_encoding) for line in input_lines)}

    proc = run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


def pipe_lines_string(engine: str, format: str, input_lines: typing.Iterator[str],
                      *, encoding: str,
                      renderer: typing.Optional[str] = None,
                      formatter: typing.Optional[str] = None,
                      quiet: bool = False) -> str:
    r"""Return ``input_lines`` piped through Graphviz ``engine``
        into ``format`` as ``str``.

    Args:
        engine: Layout engine for rendering (``'dot'``, ``'neato'``, ...).
        format: Output format for rendering (``'pdf'``, ``'png'``, ...).
        input_lines: DOT source lines to render (including final newline).
        encoding: Encoding to en/decode subprocess stdin and stdout (required).
        renderer: Output renderer (``'cairo'``, ``'gd'``, ...).
        formatter: Output formatter (``'cairo'``, ``'gd'``, ...).
        quiet: Suppress ``stderr`` output from the layout subprocess.

    Returns:
        Decoded stdout of the layout command.

    Raises:
        ValueError: If ``engine``, ``format``, ``renderer``, or ``formatter``
            are not known.
        graphviz.RequiredArgumentError: If ``formatter`` is given
            but ``renderer`` is None.
        graphviz.ExecutableNotFound: If the Graphviz 'dot' executable
            is not found.
        subprocess.CalledProcessError: If the returncode (exit status)
            of the rendering 'dot' subprocess is non-zero.

    Example:
        >>> import graphviz
        >>> graphviz.pipe_lines_string('dot', 'svg', iter(['graph { spam }\n']),
        ...                            encoding='ascii')[:14]
        '<?xml version='

    Note:
        The layout command is started from the current directory.
    """
    cmd = command(engine, format, renderer=renderer, formatter=formatter)
    kwargs = {'input_lines': input_lines, 'encoding': encoding}

    proc = run_check(cmd, capture_output=True, quiet=quiet, **kwargs)
    return proc.stdout


class Graphviz(copying.Copy):
    """Graphiz default engine/format."""

    _engine = 'dot'

    _format = 'pdf'

    _renderer = None

    _formatter = None

    @staticmethod
    def _pipe_lines(*args, **kwargs):
        """Simplify mocking ``pipe_lines``."""
        return pipe_lines(*args, **kwargs)

    @staticmethod
    def _pipe_lines_string(*args, **kwargs):
        return pipe_lines_string(*args, **kwargs)

    @staticmethod
    def _render(*args, **kwargs):
        """Simplify mocking ``render``."""
        return render(*args, **kwargs)

    @staticmethod
    def _unflatten(*args, **kwargs):
        return unflatten(*args, **kwargs)

    def __init__(self, format=None, engine=None, *,
                 renderer: typing.Optional[str] = None,
                 formatter: typing.Optional[str] = None,
                 **kwargs):
        super().__init__(**kwargs)

        if format is not None:
            self.format = format

        if engine is not None:
            self.engine = engine

        self.renderer = renderer

        self.formatter = formatter

    def _copy_kwargs(self, **kwargs):
        """Return the kwargs to create a copy of the instance."""
        attr_kw = [('_engine', 'engine'), ('_format', 'format'),
                   ('_renderer', 'renderer'), ('_formatter', 'formatter')]
        ns = self.__dict__
        for attr, kw in attr_kw:
            assert kw not in kwargs
            if attr in ns:
                kwargs[kw] = ns[attr]
        return super()._copy_kwargs(**kwargs)

    @property
    def engine(self) -> str:
        """The layout engine used for rendering
            (``'dot'``, ``'neato'``, ...)."""
        return self._engine

    @engine.setter
    def engine(self, engine: str) -> None:
        engine = engine.lower()
        if engine not in ENGINES:
            raise ValueError(f'unknown engine: {engine!r}')
        self._engine = engine

    @property
    def format(self) -> str:
        """The output format used for rendering
            (``'pdf'``, ``'png'``, ...)."""
        return self._format

    @format.setter
    def format(self, format: str) -> None:
        format = format.lower()
        if format not in FORMATS:
            raise ValueError(f'unknown format: {format!r}')
        self._format = format

    @property
    def renderer(self) -> typing.Optional[str]:
        """The output renderer used for rendering
            (``'cairo'``, ``'gd'``, ...)."""
        return self._renderer

    @renderer.setter
    def renderer(self, renderer: typing.Optional[str]) -> None:
        if renderer is None:
            self.__dict__.pop('_renderer', None)
        else:
           renderer = renderer.lower()
           if renderer not in RENDERERS:
               raise ValueError(f'unknown renderer: {renderer!r}')
           self._renderer = renderer

    @property
    def formatter(self) -> typing.Optional[str]:
        """The output formatter used for rendering
            (``'cairo'``, ``'gd'``, ...)."""
        return self._formatter

    @formatter.setter
    def formatter(self, formatter: typing.Optional[str]) -> None:
        if formatter is None:
            self.__dict__.pop('_formatter', None)
        else:
            formatter = formatter.lower()
            if formatter not in FORMATTERS:
                 raise ValueError(f'unknown formatter: {formatter!r}')
            self._formatter = formatter

    def _get_backend_kwargs(self, *,
                            format: typing.Optional[str] = None,
                            renderer: typing.Optional[str] = None,
                            formatter: typing.Optional[str] = None,
                            **kwargs):
        if format is None:
            format = self._format

        if renderer is None:
            renderer = self._renderer

        if formatter is None:
            formatter = self._formatter

        kwargs.update(format=format, renderer=renderer, formatter=formatter)

        return kwargs

    _get_pipe_kwargs = _get_render_kwargs = _get_backend_kwargs


def version() -> typing.Tuple[int, ...]:
    """Return the version number tuple
        from the ``stderr`` output of ``dot -V``.

    Returns:
        Two, three, or four ``int`` version ``tuple``.

    Raises:
        graphviz.ExecutableNotFound: If the Graphviz executable is not found.
        subprocess.CalledProcessError: If the exit status is non-zero.
        RuntimeError: If the output cannot be parsed into a version number.

    Example:
        >>> import graphviz
        >>> graphviz.version()  # doctest: +ELLIPSIS
        (...)

    Note:
        Ignores the ``~dev.<YYYYmmdd.HHMM>`` portion of development versions.

    See also:
        Graphviz Release version entry format:
        https://gitlab.com/graphviz/graphviz/-/blob/f94e91ba819cef51a4b9dcb2d76153684d06a913/gen_version.py#L17-20
    """
    cmd = [DOT_BINARY, '-V']
    log.debug('run %r', cmd)
    proc = run_check(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='ascii')

    ma = re.search(r'graphviz version'
                   r' '
                   r'(\d+)\.(\d+)'
                   r'(?:\.(\d+)'
                       r'(?:'  # noqa: E127
                           r'~dev\.\d{8}\.\d{4}'  # noqa: E127
                           r'|'
                           r'\.(\d+)'
                       r')?'
                   r')?'
                   r' ', proc.stdout)
    if ma is None:
        raise RuntimeError(f'cannot parse {cmd!r} output: {proc.stdout!r}')

    return tuple(int(d) for d in ma.groups() if d is not None)