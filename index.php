<?php
/**
 * Project bundle builder.
 *
 * Reads the current directory recursively and writes all supported text/code files
 * into one text file: ACMF_PROJECT_BUNDLE.txt
 *
 * Usage:
 *   php bundle_project.php
 */

declare(strict_types=1);

$rootDir = realpath(__DIR__);
$outputFile = $rootDir . DIRECTORY_SEPARATOR . 'ACMF_PROJECT_BUNDLE.txt';

$excludedDirs = [
    '.git',
    '.venv',
    'venv',
    'env',
    '__pycache__',
    'node_modules',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.idea',
    '.vscode',
    'dist',
    'build',
    'coverage',
    '.coverage',
];

$excludedFiles = [
    'ACMF_PROJECT_BUNDLE.txt',
    'bundle_project.php',
];

$allowedExtensions = [
    'py',
    'md',
    'txt',
    'json',
    'yaml',
    'yml',
    'toml',
    'ini',
    'cfg',
    'conf',
    'csv',
    'tsv',
    'html',
    'htm',
    'css',
    'js',
    'jsx',
    'ts',
    'tsx',
    'sh',
    'bash',
    'sql',
    'xml',
    'php',
];

$excludedExtensions = [
    'zip',
    'rar',
    '7z',
    'tar',
    'gz',
    'bz2',
    'xz',
    'pdf',
    'doc',
    'docx',
    'xls',
    'xlsx',
    'ppt',
    'pptx',
    'png',
    'jpg',
    'jpeg',
    'gif',
    'bmp',
    'tiff',
    'webp',
    'ico',
    'exe',
    'dll',
    'so',
    'dylib',
    'pyc',
    'pyo',
    'db',
    'sqlite',
    'sqlite3',
];

$maxFileSizeBytes = 2 * 1024 * 1024; // 2 MB per file

function normalizePath(string $path): string
{
    return str_replace('\\', '/', $path);
}

function relativePath(string $path, string $rootDir): string
{
    $path = normalizePath($path);
    $rootDir = normalizePath($rootDir);

    if (str_starts_with($path, $rootDir)) {
        $rel = substr($path, strlen($rootDir));
        $rel = ltrim($rel, '/');
        return './' . $rel;
    }

    return $path;
}

function isBinaryFile(string $file): bool
{
    $handle = @fopen($file, 'rb');

    if ($handle === false) {
        return true;
    }

    $chunk = fread($handle, 4096);
    fclose($handle);

    if ($chunk === false) {
        return true;
    }

    return str_contains($chunk, "\0");
}

function shouldSkipPath(
    SplFileInfo $fileInfo,
    string $rootDir,
    array $excludedDirs,
    array $excludedFiles,
    array $allowedExtensions,
    array $excludedExtensions,
    int $maxFileSizeBytes
): ?string {
    $path = $fileInfo->getPathname();
    $filename = $fileInfo->getFilename();

    if (in_array($filename, $excludedFiles, true)) {
        return 'excluded file';
    }

    $relative = relativePath($path, $rootDir);
    $parts = explode('/', normalizePath($relative));

    foreach ($parts as $part) {
        if (in_array($part, $excludedDirs, true)) {
            return 'excluded directory';
        }
    }

    if (!$fileInfo->isFile()) {
        return 'not a file';
    }

    if (!$fileInfo->isReadable()) {
        return 'not readable';
    }

    if ($fileInfo->getSize() > $maxFileSizeBytes) {
        return 'file too large';
    }

    $ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));

    if ($ext !== '' && in_array($ext, $excludedExtensions, true)) {
        return 'excluded extension';
    }

    if ($ext === '' || !in_array($ext, $allowedExtensions, true)) {
        return 'unsupported extension';
    }

    if (isBinaryFile($path)) {
        return 'binary file';
    }

    return null;
}

$iterator = new RecursiveIteratorIterator(
    new RecursiveDirectoryIterator(
        $rootDir,
        FilesystemIterator::SKIP_DOTS
    ),
    RecursiveIteratorIterator::SELF_FIRST
);

$files = [];
$skipped = [];

foreach ($iterator as $fileInfo) {
    /** @var SplFileInfo $fileInfo */
    if (!$fileInfo->isFile()) {
        continue;
    }

    $reason = shouldSkipPath(
        $fileInfo,
        $rootDir,
        $excludedDirs,
        $excludedFiles,
        $allowedExtensions,
        $excludedExtensions,
        $maxFileSizeBytes
    );

    $relative = relativePath($fileInfo->getPathname(), $rootDir);

    if ($reason !== null) {
        $skipped[] = [$relative, $reason];
        continue;
    }

    $files[] = $fileInfo->getPathname();
}

sort($files, SORT_STRING);

$out = fopen($outputFile, 'wb');

if ($out === false) {
    fwrite(STDERR, "Cannot open output file: {$outputFile}\n");
    exit(1);
}

fwrite($out, "ACMF PROJECT BUNDLE\n");
fwrite($out, "Generated: " . date('c') . "\n");
fwrite($out, "Root: {$rootDir}\n");
fwrite($out, "Files included: " . count($files) . "\n");
fwrite($out, "\n");

foreach ($files as $file) {
    $relative = relativePath($file, $rootDir);
    $content = file_get_contents($file);

    if ($content === false) {
        continue;
    }

    fwrite($out, "\n\n===== FILE: {$relative} =====\n");
    fwrite($out, $content);
    fwrite($out, "\n===== END FILE: {$relative} =====\n");
}

fwrite($out, "\n\n===== SKIPPED FILES =====\n");

foreach ($skipped as [$path, $reason]) {
    fwrite($out, "{$path} -- {$reason}\n");
}

fclose($out);

echo "Done.\n";
echo "Output file: {$outputFile}\n";
echo "Included files: " . count($files) . "\n";
echo "Skipped files: " . count($skipped) . "\n";
