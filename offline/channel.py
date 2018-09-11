import argparse
import logging
import os
import platform
import shutil
import subprocess


logging.getLogger(__name__).addHandler(logging.NullHandler())


def iter_package_dir(path: str):
    for filename in os.listdir(path):
        if filename.endswith('.tar.bz2'):
            yield filename


def copy_and_index_files(packages_path: str, channel_path: str, is_64_bit: bool):
    if is_64_bit and platform.system() == 'Windows':
        arch_sub_folder = 'win-64'
    elif not is_64_bit and platform.system() == 'Windows':
        arch_sub_folder = 'win-32'
    elif is_64_bit and platform.system() == 'Linux':
        arch_sub_folder = 'linux-64'
    elif not is_64_bit and platform.system() == 'Linux':
        arch_sub_folder = 'linux-32'
    elif is_64_bit and platform.system() == 'Darwin':
        arch_sub_folder = 'osx-64'
    else:
        err_string = 'Unrecognized or incompatible architecture for conda'
        logging.error(err_string)
        raise ValueError(err_string)

    logging.debug('Detected architecture as {0:s}'.format(arch_sub_folder))
    arch_folder = os.path.join(channel_path, arch_sub_folder)
    os.makedirs(arch_folder)

    logging.info('Copying packages from {0:s} to {1:s}'.format(packages_path, arch_folder))
    for package_file in iter_package_dir(packages_path):
        copied_name = shutil.copy(os.path.join(packages_path, package_file), arch_folder)
        logging.debug('Finished copying package to {0:s}'.format(copied_name))

    subprocess.run(['conda', 'index', channel_path])


def create_offline_channel(packages_path: str, channel_path: str, is_64_bit: bool):
    # 1. Create the channel directory if it does not exist
    if os.path.exists(channel_path):
        if os.listdir(channel_path):
            err_string = 'The channel path must be an empty or non-existent folder'
            logging.error(err_string)
            raise ValueError(err_string)
    else:
        logging.debug('Creating channel path directory {0:s}'.format(channel_path))
        os.makedirs(channel_path)

    # 2. Copy the packages to the channel path and index the packages
    copy_and_index_files(packages_path, channel_path, is_64_bit)

    logging.info('Done creating channel')


def _argparse_packages_folder(filename: str):
    if not os.path.exists(filename):
        raise argparse.ArgumentTypeError('Package path {0:s} does not exist'.format(filename))
    return os.path.realpath(filename)


def _argparse_channel_folder(filename: str):
    if os.path.exists(filename):
        if os.listdir(filename):
            raise argparse.ArgumentTypeError(
                'Channel path {0:s} must be an empty or non-existent folder'.format(filename))
    return os.path.realpath(filename)


def _main_cmdline():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description='Create an offline channel from a package folder')
    parser.add_argument('packages_folder', type=_argparse_packages_folder,
                        help='file path to packages folder')
    parser.add_argument('channel_folder', type=_argparse_channel_folder,
                        help='file path to channel folder')
    parser.add_argument('--arch', choices={32, 64}, default=64,
                        help='architecture (default to 64)')
    args = parser.parse_args()
    create_offline_channel(args.packages_folder, args.channel_folder, args.arch == 64)


if __name__ == '__main__':
    _main_cmdline()
