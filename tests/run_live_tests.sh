cd test_cisco_ios/
./test_ios.sh > ../test_out/test_cisco_ios.out 2> ../test_out/test_cisco_ios.stderr &

cd ..
cd test_cisco_nxos/
./test_cisco_nxos.sh > ../test_out/test_cisco_nxos.out 2> ../test_out/test_cisco_nxos.stderr &

cd ..
cd test_cisco_xe
./test_cisco_xe.sh > ../test_out/test_cisco_xe.out 2> ../test_out/test_cisco_xe.stderr &

cd ..
cd test_cisco_xr
./test_iosxr.sh > ../test_out/test_cisco_xr_xrv.out 2> ../test_out/test_cisco_xr_xrv.stderr &
./test_iosxr_azure.sh > ../test_out/test_cisco_xr_azure.out 2> ../test_out/test_cisco_xr_azure.stderr &

cd ..
cd test_arista_eos
./test_arista_eos.sh > ../test_out/test_arista_eos.out 2> ../test_out/test_arista_eos.stderr &

cd ..
cd test_juniper_junos
./test_juniper_junos.sh > ../test_out/test_juniper_junos.out 2> ../test_out/test_juniper_junos.stderr &

# cd ..
# cd test_cisco_asa
# ./test_cisco_asa.sh > ../test_out/test_cisco_asa.out 2> ../test_out/test_cisco_asa.stderr &
