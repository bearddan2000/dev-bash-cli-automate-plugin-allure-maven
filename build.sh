#! /bin/bash

file=$1/install.sh

build_directive=`grep mvn $file | grep clean`

build_directive="${build_directive} allure:report allure:serve"

sed -i "s/mvn clean/$build_directive/g" $file
