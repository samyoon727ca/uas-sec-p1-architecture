// P1 architecture of the notional small UAS, in SysML v2 textual notation.
// Hand-written. Element short names (<'CMP-FC'>, <'DF-01'>, ...) and the alias
// index at the end match data/elements.csv; tools/gen_sysml.py checks that
// every element ID has an alias here.
package UAS_Architecture {
    private import ScalarValues::*;

    doc /*
     * Notional, unclassified small UAS for a generic survey/ISR mission. Built
     * from public sources only (A-01). See docs/04-architecture.md.
     */

    // ---------------------------------------------------------------------
    // Items carried on data flows and held in data stores
    // ---------------------------------------------------------------------
    item def MavlinkFrame {
        doc /* MAVLink 2 frame. Signed with the shared key when signing is active (A-06). */
        attribute signed : Boolean;
    }
    item def VideoStream;
    item def Imagery;
    item def NavigationData;
    item def ActuatorCommand;
    item def GnssSignal;
    item def OperatorInput;
    item def MaintenanceCommand;
    item def SoftwareRelease { doc /* Firmware, system images, parameters or credentials loaded during maintenance. */ }
    item def SourcePackage;
    item def KeyMaterial;
    item def FlightLog;
    item def MissionData;
    item def FirmwareImage;
    item def SystemImage;
    item def ReleaseArtifact;
    item def WireGuardPacket;
    item def RfSignal;

    // ---------------------------------------------------------------------
    // Trust boundaries (section 4.1) and the metadata that marks crossings
    // ---------------------------------------------------------------------
    enum def TrustBoundary {
        enum <'TB-01'> airGroundRf;
        enum <'TB-02'> flightCriticalMissionComputing;
        enum <'TB-03'> airVehiclePhysical;
        enum <'TB-04'> gcsHost;
        enum <'TB-05'> supplyChain;
        enum <'TB-06'> gnssRf;
    }
    metadata def Crosses {
        doc /* Trust boundaries a data flow crosses. */
        attribute boundary : TrustBoundary[1..*];
    }

    // ---------------------------------------------------------------------
    // Port definitions
    // ---------------------------------------------------------------------
    port def TunnelPort {
        doc /* WireGuard tunnel endpoint between GCS and CC (DD-02). Rides on the radio link. */
        inout item frames : MavlinkFrame[0..*];
        inout item video : VideoStream[0..*];
    }
    port def EthernetPort { inout item packets : WireGuardPacket[0..*]; }
    port def RfPort { inout item signals : RfSignal[0..*]; }
    port def MavlinkUartPort {
        doc /* TB-02 interface: MAVLink 2 over UART only (DD-03). */
        inout item frames : MavlinkFrame[0..*];
    }
    port def PayloadPort { inout item imagery : Imagery[0..*]; }
    port def NavigationPort { inout item data : NavigationData[0..*]; }
    port def ActuatorPort { inout item commands : ActuatorCommand[0..*]; }
    port def GnssPort { inout item signals : GnssSignal[0..*]; }
    port def HmiPort { inout item input : OperatorInput[0..*]; }
    port def ConsolePort { inout item commands : MaintenanceCommand[0..*]; }
    port def IntakePort { inout item packages : SourcePackage[0..*]; }
    port def MaintenancePort {
        doc /* Wired maintenance connection, used on the ground only (A-14). */
        inout item loads : SoftwareRelease[0..*];
        inout item offload : MissionData[0..*];
        inout item logs : FlightLog[0..*];
    }

    // ---------------------------------------------------------------------
    // Component and external-entity definitions
    // ---------------------------------------------------------------------
    part def FlightController {
        doc /* PX4 on NuttX, Pixhawk-standard FMU (A-03, DD-06). Verifies and signs MAVLink. */
        port ccLink : MavlinkUartPort;
        port navLink : NavigationPort;
        port actuatorLink : ActuatorPort;
        port usb : MaintenancePort;
    }
    part def CompanionComputer {
        doc /* ARM64 Linux single-board computer (A-04). WireGuard endpoint, MAVLink router and command filter (DD-04). */
        port tunnel : TunnelPort;
        port radioLink : EthernetPort;
        port fcLink : MavlinkUartPort;
        port payloadLink : PayloadPort;
        port maint : MaintenancePort;
    }
    part def EoPayload { port data : PayloadPort; }
    part def NavigationModule {
        doc /* Civil GNSS receiver plus magnetometer (A-10). */
        port antenna : GnssPort;
        port fcLink : NavigationPort;
    }
    part def Actuators { port input : ActuatorPort; }
    part def DataLinkRadio {
        doc /* Generic IP radio. Untrusted transport (A-05). */
        port hostLink : EthernetPort;
        port rf : RfPort;
    }
    part def GroundControlStation {
        doc /* QGroundControl on a Linux laptop. */
        port tunnel : TunnelPort;
        port radioLink : EthernetPort;
        port hmi : HmiPort;
        port maint : MaintenancePort;
    }
    part def MaintenanceStation {
        doc /* Builds, signs and loads software; provisions keys; receives offload. Wired links only. */
        port fcMaint : MaintenancePort;
        port ccMaint : MaintenancePort;
        port gcsMaint : MaintenancePort;
        port intake : IntakePort;
        port console : ConsolePort;
    }
    part def Operator { port hmi : HmiPort; }
    part def Maintainer { port console : ConsolePort; }
    part def GnssConstellation { port signal : GnssPort; }
    part def UpstreamSources { port distribution : IntakePort; }

    // ---------------------------------------------------------------------
    // System context
    // ---------------------------------------------------------------------
    part uasSystem {
        part <'EE-OP'> operator : Operator;
        part <'EE-MNT'> maintainer : Maintainer;
        part <'EE-GNSS'> gnss : GnssConstellation;
        part <'EE-UPSTREAM'> upstream : UpstreamSources;

        part groundSegment {
            part <'CMP-GCS'> gcs : GroundControlStation {
                item <'DS-GCS-CRED'> credentials : KeyMaterial;
                item <'DS-GCS-DATA'> missionData : MissionData;
            }
            part <'CMP-RAD-G'> groundRadio : DataLinkRadio;
            connect gcs.radioLink to groundRadio.hostLink;
        }

        part airVehicle {
            doc /* Everything inside TB-03, the air vehicle's physical boundary. */
            part <'CMP-RAD-A'> airRadio : DataLinkRadio;
            part missionComputing {
                part <'CMP-CC'> cc : CompanionComputer {
                    item <'DS-CC-SYS'> systemImage : SystemImage;
                    item <'DS-CC-CRED'> credentials : KeyMaterial;
                    item <'DS-CC-DATA'> missionData : MissionData;
                }
                part <'CMP-PL'> payload : EoPayload;
            }
            part flightCritical {
                part <'CMP-FC'> fc : FlightController {
                    item <'DS-FC-KEY'> signingKeyFile : KeyMaterial;
                    item <'DS-FC-LOG'> flightLogs : FlightLog;
                    item <'DS-FC-FW'> firmwareAndParameters : FirmwareImage;
                }
                part <'CMP-NAV'> nav : NavigationModule;
                part <'CMP-ACT'> actuators : Actuators;
            }
            connect airRadio.hostLink to missionComputing.cc.radioLink;
        }

        part <'CMP-MSS'> mss : MaintenanceStation {
            item <'DS-MSS-KEYS'> keyMaterial : KeyMaterial;
            item <'DS-MSS-ART'> releaseArtifacts : ReleaseArtifact;
        }

        // The RF hop between the two radios (TB-01).
        connect groundSegment.groundRadio.rf to airVehicle.airRadio.rf;

        // Data flows (data/elements.csv). DF-01 to DF-03 are logical flows
        // inside the WireGuard tunnel, carried by the radios.
        flow <'DF-01'> c2Uplink of MavlinkFrame
            from groundSegment.gcs.tunnel to airVehicle.missionComputing.cc.tunnel {
            @Crosses { boundary = (TrustBoundary::gcsHost, TrustBoundary::airGroundRf); }
        }
        flow <'DF-02'> telemetryDownlink of MavlinkFrame
            from airVehicle.missionComputing.cc.tunnel to groundSegment.gcs.tunnel {
            @Crosses { boundary = (TrustBoundary::airGroundRf, TrustBoundary::gcsHost); }
        }
        flow <'DF-03'> videoDownlink of VideoStream
            from airVehicle.missionComputing.cc.tunnel to groundSegment.gcs.tunnel {
            @Crosses { boundary = (TrustBoundary::airGroundRf, TrustBoundary::gcsHost); }
        }
        flow <'DF-04'> ccToFcCommands of MavlinkFrame
            from airVehicle.missionComputing.cc.fcLink to airVehicle.flightCritical.fc.ccLink {
            @Crosses { boundary = TrustBoundary::flightCriticalMissionComputing; }
        }
        flow <'DF-05'> fcToCcTelemetry of MavlinkFrame
            from airVehicle.flightCritical.fc.ccLink to airVehicle.missionComputing.cc.fcLink {
            @Crosses { boundary = TrustBoundary::flightCriticalMissionComputing; }
        }
        flow <'DF-06'> payloadImagery of Imagery
            from airVehicle.missionComputing.payload.data to airVehicle.missionComputing.cc.payloadLink;
        flow <'DF-07'> gnssSignals of GnssSignal
            from gnss.signal to airVehicle.flightCritical.nav.antenna {
            @Crosses { boundary = TrustBoundary::gnssRf; }
        }
        flow <'DF-08'> navigationData of NavigationData
            from airVehicle.flightCritical.nav.fcLink to airVehicle.flightCritical.fc.navLink;
        flow <'DF-09'> actuatorCommands of ActuatorCommand
            from airVehicle.flightCritical.fc.actuatorLink to airVehicle.flightCritical.actuators.input;
        flow <'DF-10'> operatorInput of OperatorInput
            from operator.hmi to groundSegment.gcs.hmi {
            @Crosses { boundary = TrustBoundary::gcsHost; }
        }
        flow <'DF-11'> fcMaintenanceLoad of SoftwareRelease
            from mss.fcMaint to airVehicle.flightCritical.fc.usb {
            @Crosses { boundary = TrustBoundary::airVehiclePhysical; }
        }
        flow <'DF-12'> ccMaintenanceLoad of SoftwareRelease
            from mss.ccMaint to airVehicle.missionComputing.cc.maint {
            @Crosses { boundary = TrustBoundary::airVehiclePhysical; }
        }
        flow <'DF-13'> gcsProvisioning of SoftwareRelease
            from mss.gcsMaint to groundSegment.gcs.maint {
            @Crosses { boundary = TrustBoundary::gcsHost; }
        }
        flow <'DF-14'> ccDataOffload of MissionData
            from airVehicle.missionComputing.cc.maint to mss.ccMaint {
            @Crosses { boundary = TrustBoundary::airVehiclePhysical; }
        }
        flow <'DF-15'> fcLogOffload of FlightLog
            from airVehicle.flightCritical.fc.usb to mss.fcMaint {
            @Crosses { boundary = TrustBoundary::airVehiclePhysical; }
        }
        flow <'DF-16'> upstreamIntake of SourcePackage
            from upstream.distribution to mss.intake {
            @Crosses { boundary = TrustBoundary::supplyChain; }
        }
        flow <'DF-17'> maintainerActions of MaintenanceCommand
            from maintainer.console to mss.console;
    }

    // ---------------------------------------------------------------------
    // Element ID index: one alias per element in data/elements.csv
    // (trust boundaries are the TrustBoundary literals above).
    // ---------------------------------------------------------------------
    alias 'CMP-FC' for uasSystem::airVehicle::flightCritical::fc;
    alias 'CMP-CC' for uasSystem::airVehicle::missionComputing::cc;
    alias 'CMP-PL' for uasSystem::airVehicle::missionComputing::payload;
    alias 'CMP-NAV' for uasSystem::airVehicle::flightCritical::nav;
    alias 'CMP-ACT' for uasSystem::airVehicle::flightCritical::actuators;
    alias 'CMP-RAD-A' for uasSystem::airVehicle::airRadio;
    alias 'CMP-RAD-G' for uasSystem::groundSegment::groundRadio;
    alias 'CMP-GCS' for uasSystem::groundSegment::gcs;
    alias 'CMP-MSS' for uasSystem::mss;
    alias 'EE-OP' for uasSystem::operator;
    alias 'EE-MNT' for uasSystem::maintainer;
    alias 'EE-GNSS' for uasSystem::gnss;
    alias 'EE-UPSTREAM' for uasSystem::upstream;
    alias 'DS-FC-KEY' for uasSystem::airVehicle::flightCritical::fc::signingKeyFile;
    alias 'DS-FC-LOG' for uasSystem::airVehicle::flightCritical::fc::flightLogs;
    alias 'DS-FC-FW' for uasSystem::airVehicle::flightCritical::fc::firmwareAndParameters;
    alias 'DS-CC-SYS' for uasSystem::airVehicle::missionComputing::cc::systemImage;
    alias 'DS-CC-CRED' for uasSystem::airVehicle::missionComputing::cc::credentials;
    alias 'DS-CC-DATA' for uasSystem::airVehicle::missionComputing::cc::missionData;
    alias 'DS-GCS-CRED' for uasSystem::groundSegment::gcs::credentials;
    alias 'DS-GCS-DATA' for uasSystem::groundSegment::gcs::missionData;
    alias 'DS-MSS-KEYS' for uasSystem::mss::keyMaterial;
    alias 'DS-MSS-ART' for uasSystem::mss::releaseArtifacts;
    alias 'DF-01' for uasSystem::c2Uplink;
    alias 'DF-02' for uasSystem::telemetryDownlink;
    alias 'DF-03' for uasSystem::videoDownlink;
    alias 'DF-04' for uasSystem::ccToFcCommands;
    alias 'DF-05' for uasSystem::fcToCcTelemetry;
    alias 'DF-06' for uasSystem::payloadImagery;
    alias 'DF-07' for uasSystem::gnssSignals;
    alias 'DF-08' for uasSystem::navigationData;
    alias 'DF-09' for uasSystem::actuatorCommands;
    alias 'DF-10' for uasSystem::operatorInput;
    alias 'DF-11' for uasSystem::fcMaintenanceLoad;
    alias 'DF-12' for uasSystem::ccMaintenanceLoad;
    alias 'DF-13' for uasSystem::gcsProvisioning;
    alias 'DF-14' for uasSystem::ccDataOffload;
    alias 'DF-15' for uasSystem::fcLogOffload;
    alias 'DF-16' for uasSystem::upstreamIntake;
    alias 'DF-17' for uasSystem::maintainerActions;
}
