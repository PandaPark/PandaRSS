#!/usr/bin/python

from setuptools import setup, find_packages
import pandarss

install_requires = [
    'Twisted>=15.0.0',
    'bottle>=0.12.7'
]

package_data={
  'pandarss': [
        'views/css/*',
        'views/js/*',
        'views/*'
    ]
}


setup(name='pandarss',
      version='0.1',
      author='pandaman',
      author_email='pandaman1999@foxmail.com',
      url='https://github.com/PandaPark/PandaRSS',
      license='BSD',
      description='ToughRADIUS Self-service Portal',
      long_description=open('README.md').read(),
      classifiers=[
       'Development Status :: 6 - Mature',
       'Intended Audience :: Developers',
       'Programming Language :: Python :: 2.7',
       'Topic :: Software Development :: Libraries :: Python Modules',
       'Topic :: System :: Systems Administration :: Authentication/Directory',
       ],
      packages=find_packages(),
      package_data=package_data,
      keywords=['radius','toughradius','self-service ','pandarss'],
      zip_safe=True,
      include_package_data=True,
      eager_resources=['pandarss'],
      install_requires=install_requires,
      entry_points={
          'console_scripts': [
              'pandarss = pandarss.main:main',
              'pandarss_txrun = pandarss.txrun:txrun',
          ]
      }
)