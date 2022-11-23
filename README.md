Timestamp transmission gateway - part of the software defined monitoring system. Python 2.7 features used.

Time sender features:
 
- getting the timestamp from the system hours of execution of the transmitting part (local) to transmit the time label on the server of the receiving part
- establishing the correction of the time label according to the calculated formula to ensure high accuracy of synchronization of the system watches of the server execution of the transmitting and receiving part;
- sending a time label taking into account the correction - values of the delay in passing data through a unilateral gateway, to set the exact time on the server of execution of the receiving part;
- providing the administrator with the possibility of choosing the method of calculating the transmitted time correction value (values of the passage of data through the server), to increase the accuracy of adjusting the system watches on the server of the receiving part;
- carrying out a periodic check of the functioning of the gateway to ensure the possibility of transmitting timestamp;
- monitoring the continuity of the sequence of transmitted packages to ensure the continuity of the receipt of accurate timestamp;
- maintaining a journal with archiving and cleaning to ensure the possibility of identifying important events in the process of functioning;
- Providing statistical information for the software complex “System of Monitoring and Management of Complexes of the Unified Time” on the functioning of the component for the possibility of analyzing the functioning


Time receiver features:

- receiving the timestamp through a restrictive one-way gateway for the transmission of the time label from the server execution of the transmitting part and bringing the system hours of the server execution of the receiving part in accordance with the resulting tag of the time
- monitoring the continuity of the sequence of taken packages to ensure the continuity of the receipt of accurate marks of time
- maintaining a journal with archiving and cleaning, to ensure the possibility of identifying important events in the process of functioning
