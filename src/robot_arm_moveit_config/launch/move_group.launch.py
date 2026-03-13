# move_group.launch.py
#
# 启动 MoveIt2 的 move_group 核心节点，加载机器人的所有规划配置。

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro


def load_yaml(package_name, file_path):
    full_path = os.path.join(get_package_share_directory(package_name), file_path)
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)


def generate_launch_description():
    moveit_config_pkg = 'robot_arm_moveit_config'
    robot_arm_pkg = 'robot_arm_demo'

    # --- 机器人描述模型 ---
    urdf_file = os.path.join(
        get_package_share_directory(robot_arm_pkg), 'urdf', '6_axis_arm.urdf.xacro')
    doc = xacro.process_file(urdf_file)
    robot_description = doc.toxml()

    robot_description_param = {'robot_description': robot_description}

    # --- SRDF 语义描述 ---
    srdf_file = os.path.join(
        get_package_share_directory(moveit_config_pkg), 'config', '6_axis_arm.srdf')
    with open(srdf_file, 'r') as f:
        srdf_content = f.read()

    robot_description_semantic = {'robot_description_semantic': srdf_content}

    # --- 运动学求解器 ---
    kinematics_yaml = load_yaml(moveit_config_pkg, 'config/kinematics.yaml')
    robot_description_kinematics = {'robot_description_kinematics': kinematics_yaml}

    # --- 关节限制 ---
    joint_limits_yaml = load_yaml(moveit_config_pkg, 'config/joint_limits.yaml')
    robot_description_planning = {'robot_description_planning': joint_limits_yaml}

    # --- OMPL 运动规划管道 ---
    ompl_yaml = load_yaml(moveit_config_pkg, 'config/ompl_planning.yaml')
    ompl_planning_pipeline_config = {
        'planning_pipelines': ['ompl'],
        'ompl': ompl_yaml,
    }

    # --- MoveIt 控制器接口 ---
    moveit_controllers_yaml = load_yaml(moveit_config_pkg, 'config/moveit_controllers.yaml')
    moveit_controllers = {
        'moveit_controller_manager': 'moveit_simple_controller_manager/MoveItSimpleControllerManager',
    }
    moveit_controllers.update(moveit_controllers_yaml)

    # --- 轨迹执行配置 ---
    trajectory_execution = {
        'moveit_manage_controllers': True,
        'trajectory_execution.allowed_execution_duration_scaling': 1.2,
        'trajectory_execution.allowed_goal_duration_margin': 0.5,
        'trajectory_execution.allowed_start_tolerance': 0.01,
    }

    # --- Move Group 核心节点 ---
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            robot_description_param,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            ompl_planning_pipeline_config,
            moveit_controllers,
            trajectory_execution,
            {'use_sim_time': True},
        ],
    )

    # --- 机器人状态发布节点 ---
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description_param, {'use_sim_time': True}],
    )

    return LaunchDescription([
        robot_state_publisher,
        move_group_node,
    ])
